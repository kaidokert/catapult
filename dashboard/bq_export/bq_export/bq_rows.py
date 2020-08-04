# Copyright (c) 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Export chromeperf Row data to BigQuery with Beam & Cloud Dataflow."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import json
import logging
import re
import zlib

import apache_beam as beam
from apache_beam.options.pipeline_options import DebugOptions
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.metrics import Metrics
from apache_beam.transforms.core import FlatMap
from google.cloud.datastore import client as ds_client
from google.cloud.datastore import query as ds_query
from google.cloud.datastore import key as ds_key

from bq_export.split_by_timestamp import ReadTimestampRangeFromDatastore
from bq_export.export_options import BqExportOptions
from bq_export.utils import (FloatHack, PrintCounters,
                             WriteToPartitionedBigQuery)


# BigQuery table names may only have letters, numbers, and underscore.
_INVALID_BQ_TABLE_NAME_CHARS_RE = re.compile('[^a-zA-Z0-9_]')


def main():
  project = 'chromeperf'
  options = PipelineOptions()
  options.view_as(DebugOptions).add_experiment('use_beam_bq_sink')
  options.view_as(GoogleCloudOptions).project = project
  bq_export_options = options.view_as(BqExportOptions)

  p = beam.Pipeline(options=options)
  entities_read = Metrics.counter('main', 'entities_read')
  failed_entity_transforms = Metrics.counter('main', 'failed_entity_transforms')

  """
  CREATE TABLE `chromeperf.chromeperf_dashboard_rows.<MASTER>`
  (revision INT64 NOT NULL,
   value FLOAT64 NOT NULL,
   std_error FLOAT64,
   `timestamp` TIMESTAMP NOT NULL,
   master STRING NOT NULL,
   bot STRING NOT NULL,
   measurement STRING,
   test STRING NOT NULL,
   properties STRING,
   sample_values ARRAY<FLOAT64>)
  PARTITION BY DATE(`timestamp`)
  CLUSTER BY master, bot, measurement;
  """  # pylint: disable=pointless-string-statement
  bq_row_schema = {'fields': [
      {'name': 'revision', 'type': 'INT64', 'mode': 'REQUIRED'},
      {'name': 'value', 'type': 'FLOAT', 'mode': 'REQUIRED'},
      {'name': 'std_error', 'type': 'FLOAT', 'mode': 'NULLABLE'},
      {'name': 'timestamp', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
      {'name': 'master', 'type': 'STRING', 'mode': 'REQUIRED'},
      {'name': 'bot', 'type': 'STRING', 'mode': 'REQUIRED'},
      {'name': 'measurement', 'type': 'STRING', 'mode': 'NULLABLE'},
      {'name': 'test', 'type': 'STRING', 'mode': 'REQUIRED'},
      {'name': 'properties', 'type': 'STRING', 'mode': 'NULLABLE'},
      {'name': 'sample_values', 'type': 'FLOAT', 'mode': 'REPEATED'},
  ]}
  def RowEntityToRowDict(entity):
    entities_read.inc()
    try:
      d = {
          'revision': entity.key.id,
          'value': FloatHack(entity['value']),
          'std_error': FloatHack(entity.get('error')),
          'timestamp': entity['timestamp'].isoformat(),
          'test': entity.key.parent.name,
      }
      # Add the expando properties as a JSON-encoded dict.
      properties = {}
      for key, value in entity.items():
        if key in d or key in ['parent_test', 'error']:
          # skip properties with dedicated columns.
          continue
        if isinstance(value, float):
          value = FloatHack(value)
        properties[key] = value
      d['properties'] = json.dumps(properties) if properties else None
      # Add columns derived from test: master, bot.
      test_path_parts = d['test'].split('/', 2)
      if len(test_path_parts) >= 3:
        d['master'] = test_path_parts[0]
        d['bot'] = test_path_parts[1]
        d['measurement'] = '/'.join(test_path_parts[2:])
      return [d]
    except KeyError:
      logging.getLogger().exception('Failed to convert Row')
      failed_entity_transforms.inc()
      return []

  row_query_params = dict(project=project, kind='Row')
  row_entities = (
      p
      | 'ReadFromDatastore(Row)' >> ReadTimestampRangeFromDatastore(
          row_query_params,
          time_range_provider=bq_export_options.GetTimeRangeProvider(),
          step=datetime.timedelta(minutes=5)))

  row_dicts = (
      row_entities | 'ConvertEntityToDict(Row)' >> FlatMap(RowEntityToRowDict))


  def HistogramEntityToDict(entity):
    entities_read.inc()
    try:
      data = entity['data']
    except KeyError:
      logging.getLogger().exception('Histogram missing "data" field')
      failed_entity_transforms.inc()
      return []
    try:
      json_str = zlib.decompress(data)
    except zlib.error:
      logging.getLogger().exception('Histogram data not valid zlib: ' + repr(data))
      failed_entity_transforms.inc()
      return []
    try:
      data_dict = json.loads(json_str)
    except json.JSONDecodeError:
      logging.getLogger().exception('Histogram data not valid json.')
      failed_entity_transforms.inc()
      return []
    sample_values = data_dict.get('sampleValues', [])
    if not isinstance(sample_values, list):
      logging.getLogger().exception('Histogram data.sampleValues not valid list.')
      failed_entity_transforms.inc()
      return []
    count = len(sample_values)
    sample_values = [v for v in sample_values if v is not None]
    if len(sample_values) != count:
        logging.getLogger().warn(
            'Histogram data.sampleValues contains null: ' + repr(entity.key))
    for v in sample_values:
      if not isinstance(v, (int, float)):
        logging.getLogger().exception(
            'Histogram data.sampleValues contains non-numeric: ' + repr(v))
        failed_entity_transforms.inc()
        return []
    try:
      return [{
          'test': entity['test'].name,
          'revision': entity['revision'],
          'sample_values': sample_values,
      }]
    except KeyError:
      logging.getLogger().exception('Histogram missing test or revision field/s')
      failed_entity_transforms.inc()
      return []

  histogram_query_params = dict(project=project, kind='Histogram')
  histogram_entities = (
      p
      | 'ReadFromDatastore(Histogram)' >> ReadTimestampRangeFromDatastore(
          histogram_query_params,
          time_range_provider=bq_export_options.GetTimeRangeProvider(),
          step=datetime.timedelta(minutes=5)))

  histogram_dicts = (
      histogram_entities | 'ConvertEntityToDict(Histogram)' >> FlatMap(HistogramEntityToDict))

  def TestRevision(element):
    #logging.getLogger().info('revision: {}, test: {}'.format(element['revision'], element['test']))
    return (element['test'], element['revision'])

  rows_with_key = (
      row_dicts | 'WithKeys(Row)' >> beam.WithKeys(TestRevision)
  )
  histograms_with_key = (
      histogram_dicts | 'WithKeys(Histogram)' >> beam.WithKeys(TestRevision)
  )



##  #def RowKeys(k_v):
##  #  logging.getLogger().info('k: {}, type(v): {}'.format(k_v[0], str(type(k_v[1]))))
##  #  return k_v[0]
##
##
##  #def MinMax(values):
##  #  logging.getLogger().info('values: ' + repr(values))
##  #  return (min(values), max(values))
##
##  rows_with_key = (
##      row_dicts | 'WithKeys(Row)' >> beam.WithKeys(TestRevision)
##  )
##  test_and_revision = (
##      rows_with_key
##      # Strip down to just the test,revision tuples.
##      #| 'RowKeys' >> beam.Map(RowKeys)
##      | 'RowKeys' >> beam.Keys()
##      #| beam.CombinePerKey(lambda rs: (min(rs), max(rs)))
##      # Reduce to test,min_rev,max_rev
##  )
##  minmax_by_test = (
##      {'min': (test_and_revision | 'CombinePerKey(min)' >> beam.CombinePerKey(min)),
##       'max': (test_and_revision | 'CombinePerKey(max)' >> beam.CombinePerKey(max))}
##      | 'MinMaxByTest' >> beam.CoGroupByKey()
##  )
##
##  histogram_dicts = (
##      minmax_by_test
##      | ReadHistogramsForRowsFromDatastore()
##      | 'ConvertHistogramEntityToDict' >> FlatMap(HistogramEntityToDict)
##  )
##  histograms_with_key = (
##      histogram_dicts | 'WithKeys(Histogram)' >> beam.WithKeys(TestRevision)
##  )

  def MergeRowAndSampleValues(element):
    key, join_values = element
    rows, histograms = join_values
    if len(rows) != 1:
      logging.getLogger().exception("conflicting rows")
      return rows
    row = rows[0]
    if len(histograms) > 1:
      logging.getLogger().exception("conflicting histograms")
      return [row]
    if len(histograms) == 0:
      # No sample values to annotate the row with
      return [row]
    histogram = histograms[0]
    row['sample_values'] = histogram['sample_values']
    return [row]

  joined_and_annotated = (
      (rows_with_key, histograms_with_key)
      | beam.CoGroupByKey()
      | beam.FlatMap(MergeRowAndSampleValues)
  )

  def TableNameFn(element):
    """Write each element to a table based on the table name."""
    master = _INVALID_BQ_TABLE_NAME_CHARS_RE.sub('_', element['master'])
    return '{project}:{dataset}.{master}{suffix}'.format(
        project=project, dataset=bq_export_options.dataset.get(), master=master,
        suffix=bq_export_options.table_suffix)

  _ = (
      joined_and_annotated
      | 'WriteToBigQuery(rows)' >> WriteToPartitionedBigQuery(TableNameFn,
                                                              bq_row_schema)
  )

  result = p.run()
  result.wait_until_finish()
  PrintCounters(result)


class ReadHistogramsForRowsFromDatastore(beam.PTransform):
  def expand(self, pcoll):
    cls = ReadHistogramsForRowsFromDatastore
    return (
        pcoll
        | 'BuildHistogramQuery' >> beam.Map(cls._FilterForTestAndMinMaxRevision)
        | 'ReadHistograms' >> beam.ParDo(cls._QueryFn())
    )

  class _QueryFn(beam.DoFn):
    def process(self, filters):
      logging.getLogger().info('filters: ' + repr(filters))
      client = ds_client.Client(project='chromeperf')
      query = ds_query.Query(client=client, kind='Histogram', filters=filters)
      for entity in query.fetch(client=client, eventual=False):
        yield entity

  @staticmethod
  def _FilterForTestAndMinMaxRevision(element):
    test_name, rev_info = element
    min_rev, max_rev = rev_info['min'], rev_info['max']
    test_key = ds_key.Key('TestMetadata', test_name, project='chromeperf')
    logging.getLogger().info('min_rev: {}, max_rev: {}, test_key: {}'.format(min_rev, max_rev, test_key))
    filters = [('test', '=', test_key)]
    if len(min_rev) > 0:
      filters.append(('revision', '>=', min_rev[0]))
    if len(max_rev) > 0:
      filters.append(('revision', '<=', max_rev[0]))
    return filters

