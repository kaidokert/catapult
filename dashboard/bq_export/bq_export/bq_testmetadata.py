# Copyright (c) 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Export TestMetadata snapshot data to BigQuery with Beam & Cloud Dataflow."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import apache_beam as beam
from apache_beam.io.gcp.datastore.v1new.datastoreio import ReadFromDatastore
from apache_beam.io.gcp.datastore.v1new.types import Query
from apache_beam.options.pipeline_options import DebugOptions
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.metrics import Metrics

from bq_export.export_options import BqExportOptions
from bq_export.utils import (PrintCounters, ConvertEntity,
                             UnconvertibleEntityError)


_IMPROVEMENT_DIRECTION = {
    0: 'UP',
    1: 'DOWN',
    # 4: 'UNKNOWN' is mapped to None/NULL, so omit it here.
}


def ValidateTestMetadataKey(key):
  """Raise if key doesn't appear to be a valid TestMetadata key.

  TestMetadata entity keys are expected to have just one path element (of kind
  'TestMetadata').  Raise UnconvertibleEntityError this key doesn't conform.
  """
  if len(key.path_elements) != 2 or key.path_elements[0] != 'TestMetadata':
    raise UnconvertibleEntityError("Unexpected format for TestMetadata key: " +
                                   repr(key))



def TestMetadataEntityToRowDict(entity):
  ValidateTestMetadataKey(entity.key)
  props = entity.properties
  try:
    d = {
        'test': entity.key.path_elements[1],
        'internal_only': props.get('internal_only', False),
        # TODO: overridden_anomaly_config,
        'improvement_direction': _IMPROVEMENT_DIRECTION.get(
            props.get('improvement_direction')),
        'units': props.get('units'),
        'has_rows': props.get('has_rows', False),
        'deprecated': props.get('deprecated', False),
        'description': props.get('description'),
        'unescaped_story_name': props.get('unescaped_story_name'),
    }
  except KeyError as e:
    raise UnconvertibleEntityError('Missing property: ' + str(e))
  # Computed properties, directly translated from the ComputedProperty
  # definitions of the ndb.Model.
  parts = d['test'].split('/')
  if len(parts) < 3:
    raise UnconvertibleEntityError(
        'Test path has too few parts: ' + d['test'])
  if len(parts) >= 4:
    d['parent'] = '/'.join(parts[:-1])
  # These correspond to the columns of the same names in the Rows export.
  d['master'] = parts[0]
  d['bot'] = parts[1]
  d['measurement'] = '/'.join(parts[2:])
  return d


def main():
  project = 'chromeperf'
  options = PipelineOptions()
  options.view_as(DebugOptions).add_experiment('use_beam_bq_sink')
  options.view_as(GoogleCloudOptions).project = project
  bq_export_options = options.view_as(BqExportOptions)

  p = beam.Pipeline(options=options)
  entities_read = Metrics.counter('main', 'entities_read')
  failed_entity_transforms = Metrics.counter('main', 'failed_entity_transforms')

  test_metadata_entities = (
      p
      | 'ReadFromDatastore(TestMetadata)' >> ReadFromDatastore(
          Query(project=project, kind='TestMetadata')))

  test_metadata_rows = (
      test_metadata_entities
      | 'ConvertEntityToRow(TestMetadata)' >> beam.FlatMap(
          ConvertEntity(TestMetadataEntityToRowDict, entities_read,
                        failed_entity_transforms))
  )

  """
  CREATE TABLE `chromeperf.chromeperf_dashboard_data.test_metadata`
  (test STRING NOT NULL,
   internal_only BOOLEAN NOT NULL,
   improvement_direction STRING,
   units STRING,
   has_rows BOOLEAN NOT NULL,
   deprecated BOOLEAN NOT NULL,
   description STRING,
   unescaped_story_name STRING,
   parent STRING,
   master STRING NOT NULL,
   bot STRING NOT NULL,
   measurement STRING NOT NULL,
   )
  CLUSTER BY test;
  """  # pylint: disable=pointless-string-statement
  bq_testmetadata_schema = {
      'fields': [
          # 'test' corresponds to the same column in the Rows export.
          {'name': 'test', 'type': 'STRING', 'mode': 'REQUIRED'},
          {'name': 'internal_only', 'type': 'BOOLEAN', 'mode': 'REQUIRED'},
          {'name': 'improvement_direction', 'type': 'STRING',
           'mode': 'NULLABLE'},
          {'name': 'units', 'type': 'STRING', 'mode': 'NULLABLE'},
          {'name': 'has_rows', 'type': 'BOOLEAN', 'mode': 'REQUIRED'},
          {'name': 'deprecated', 'type': 'BOOLEAN', 'mode': 'REQUIRED'},
          {'name': 'description', 'type': 'STRING', 'mode': 'NULLABLE'},
          {'name': 'unescaped_story_name', 'type': 'STRING',
           'mode': 'NULLABLE'},
          {'name': 'parent', 'type': 'STRING', 'mode': 'NULLABLE'},
          # Master, bot, and measurement correspond to same columns in the Rows
          # export.
          {'name': 'master', 'type': 'STRING', 'mode': 'REQUIRED'},
          {'name': 'bot', 'type': 'STRING', 'mode': 'REQUIRED'},
          {'name': 'measurement', 'type': 'STRING', 'mode': 'REQUIRED'},
      ],
  }

  def TableNameFn(unused_element):
    return '{project}:{dataset}.test_metadata{suffix}'.format(
        project=project,
        dataset=bq_export_options.dataset.get(),
        suffix=bq_export_options.table_suffix)

  _ = (
      test_metadata_rows
      | 'WriteToBigQuery(test_metadata)' >> beam.io.WriteToBigQuery(
          TableNameFn,
          schema=bq_testmetadata_schema,
          method=beam.io.WriteToBigQuery.Method.FILE_LOADS,
          write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
          create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
          additional_bq_parameters={'clustering': {'fields': ['test']}})
  )

  result = p.run()
  result.wait_until_finish()
  PrintCounters(result)

