# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Export chromeperf Row data to BigQuery with Beam & Cloud Dataflow."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import json
import logging

import apache_beam as beam
from apache_beam.io.gcp.gcsio import GcsIO
from apache_beam.io.gcp.datastore.v1new.datastoreio import ReadFromDatastore
from apache_beam.io.gcp.datastore.v1new.types import Query
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.metrics import Metrics
from apache_beam.transforms.core import FlatMap
from skia_export.split_by_timestamp import ReadTimestampRangeFromDatastore
from skia_export.export_options import ExportOptions
from skia_export.utils import FloatHack
from skia_export.skia_converter import ConvertRowsToSkiaPerf


def main():
  project = 'chromeperf'
  options = PipelineOptions()
  options.view_as(GoogleCloudOptions).project = project
  export_options = options.view_as(ExportOptions)

  p = beam.Pipeline(options=options)
  row_entities_read = Metrics.counter('main', 'row_entities_read')
  test_entities_read = Metrics.counter('main', 'test_entities_read')
  failed_row_entity_transforms = Metrics.counter(
      'main', 'failed_row_entity_transforms')
  failed_test_entity_transforms = Metrics.counter(
      'main', 'failed_test_entity_transforms')
  row_groups = Metrics.counter('main', 'row_groups')
  non_chromium_rows = Metrics.counter('main', 'non_chromium_rows')
  merge_errors = Metrics.counter('main', 'merge_errors')
  merged_rows = Metrics.counter('main', 'merged_rows')
  public_writes = Metrics.counter('main', 'public_writes')
  non_public_writes = Metrics.counter('main', 'non_public_writes')
  converted_rows = Metrics.counter('main', 'converted_rows')
  empty_bot_ids = Metrics.counter('main', 'empty_bot_ids')

  def RowEntityToDict(entity):
    row_entities_read.inc()
    try:
      d = {
          'revision': entity.key.id,
          'value': FloatHack(entity['value']),
          'error': FloatHack(entity.get('error')),
          'test': entity.key.parent.name,
          'timestamp': entity['timestamp'].strftime('%Y/%m/%d/%H'),
          'a_bot_id': '',
      }
      # Add the expando properties as a JSON-encoded dict.
      for key, value in entity.items():
        if key == 'a_bot_id':
          bot_list = sorted(value)
          d[key] = (',').join(bot_list)
          continue
        if key in d or key in ['parent_test', 'error']:
          # skip properties with dedicated columns.
          continue
        if isinstance(value, float):
          value = FloatHack(value)
        d[key] = value
      # Add columns derived from test: master, bot.
      test_path_parts = d['test'].split('/')
      if len(test_path_parts) >= 3:
        d['master_name'] = test_path_parts[0]
        d['bot_name'] = test_path_parts[1]
        d['suite_name'] = test_path_parts[2]
      if not d['a_bot_id']:
        empty_bot_ids.inc()
      return [d]
    except KeyError:
      logging.getLogger().exception('Failed to convert Row')
      failed_row_entity_transforms.inc()
      return []

  def HasRCommitPos(row):
    has_commit_pos = 'r_commit_pos' in row.keys()
    if not has_commit_pos:
      non_chromium_rows.inc()
    return has_commit_pos

  time_range_provider = export_options.GetTimeRangeProvider()

  row_query_params = dict(project=project, kind='Row')
  row_dicts = (
      p
      | 'ReadFromDatastore(Row)' >> ReadTimestampRangeFromDatastore(
          row_query_params,
          time_range_provider=time_range_provider,
          step=datetime.timedelta(minutes=5))
      | 'Filter Non-Chromium Rows' >> beam.Filter(HasRCommitPos)
      | 'ConvertEntityToDict(Row)' >> FlatMap(RowEntityToDict))

  def TestMetadataEntityToDict(entity):
    test_entities_read.inc()
    props = entity.properties
    try:
      d = {
          'test': entity.key.path_elements[1],
          'internal_only': props.get('internal_only', False),
          'improvement_direction': props.get('improvement_direction'),
          'units': props.get('units'),
      }
      return [d]
    except KeyError:
      logging.getLogger().exception('Failed to convert TestMetadata')
      failed_test_entity_transforms.inc()
      return []

  test_metadata_dicts = (
      p
      | 'ReadFromDatastore(TestMetadata)' >> ReadFromDatastore(
          Query(project=project, kind='TestMetadata'))
      |
      'ConvertEntityToDict(TestMetadata)' >> FlatMap(TestMetadataEntityToDict))

  def MergeRowAndTestMetadata(element):
    group_key, join_values = element
    rows, tests = join_values
    if len(tests) == 0:
      merge_errors.inc()
      logging.getLogger().error('No TestMetadata for test (%s)', group_key)
      return []
    if len(tests) > 1:
      merge_errors.inc()
      logging.getLogger().error('Multiple TestMetadata for test (%s)',
                                group_key)
      return []
    test = tests[0]
    if len(rows) == 0:
      return []
    for row in rows:
      for key, value in test.items():
        if key not in row.keys():
          row[key] = value
      merged_rows.inc()
    return rows

  def TestKey(entity):
    return entity['test']

  def RowKey(row):
    return (row['master_name'], row['bot_name'], row['suite_name'],
            row['r_commit_pos'], row['a_bot_id'], row['internal_only'], row['timestamp'])

  rows_with_keys = (
      row_dicts | 'WithKeys(TestKey)(Row)' >> beam.WithKeys(TestKey))

  test_metadata_with_keys = (
      test_metadata_dicts
      | 'WithKeys(TestKey)(TestMetadata)' >> beam.WithKeys(TestKey))

  def ConvertGroupedRowsToSkiaPerf(element):
    row_groups.inc()
    key, rows = element
    converted_rows.inc(len(rows))

    key_dict = {
        'master': key[0],
        'bot': key[1],
        'benchmark': key[2],
        'commit_position': key[3],
        'bot_id': key[4],
        'internal_only': key[5],
        'timestamp': key[6],
    }
    return [{
        'skia_data': ConvertRowsToSkiaPerf(
            rows,
            master=key_dict['master'],
            bot=key_dict['bot'],
            benchmark=key_dict['benchmark'],
            commit_position=key_dict['commit_position']
        ),
        'key_dict': key_dict,
    }]

  class WriteSkiaPerfBucket(beam.DoFn):

    def process(self, element):
      key = element['key_dict']
      skia_data = element['skia_data']

      if key['internal_only']:
        bucket_name = 'chrome-perf-non-public'
        non_public_writes.inc()
      else:
        bucket_name = 'chrome-perf-public'
        public_writes.inc()
      test_path = '%s/%s/%s/%s.json' % (key['master'], key['bot'],
                                        key['benchmark'],
                                        '-'.join([str(key['commit_position']), key['bot_id']]))
      filename = 'gs://%s/ingest/%s/%s' % (bucket_name, key['timestamp'],
                                           test_path)
      if export_options.testing.get() == 'no':
        with GcsIO().open(
            filename, mode='w', mime_type='application/json') as file:
          file.write(json.dumps(skia_data).encode('utf-8'))
      else:
        logging.getLogger().info(filename)
        logging.getLogger().info(skia_data)

  _ = ((rows_with_keys, test_metadata_with_keys)
       | 'CoGroupByKey' >> beam.CoGroupByKey()
       | 'MergeRowAndTestMetadata' >> beam.FlatMap(MergeRowAndTestMetadata)
       | 'WithKeys(RowKey)' >> beam.WithKeys(RowKey)
       | 'GroupByKeys(Row)' >> beam.GroupByKey()
       | 'ConvertRowsToSkiaPerf' >> beam.FlatMap(ConvertGroupedRowsToSkiaPerf)
       | 'WriteSkiaPerfBucket' >> beam.ParDo(WriteSkiaPerfBucket()))

  result = p.run()
  result.wait_until_finish()
