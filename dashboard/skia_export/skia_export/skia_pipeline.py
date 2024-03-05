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
import random
import string

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

REPOSITORY_PROPERTY_MAP = {
  'chromium': {
    'masters': ['ChromeFYIInternal', 'ChromiumAndroid', 'ChromiumChrome',
    'ChromiumChromiumos', 'ChromiumClang', 'ChromiumFuchsia', 'ChromiumGPUFYI',
    'ChromiumPerf', 'ChromiumPerfFyi', 'ChromiumPerfPGO', 'TryServerChromiumFuchsia',
    'TryserverChromiumChromiumOS', 'ChromiumFuchsiaFyi', 'TryserverChromiumAndroid',
    'ChromiumAndroidFyi', 'ChromiumFYI', 'ChromiumPerfFyi.all'],
    'public_bucket_name': 'chrome-perf-public',
    'internal_bucket_name': 'chrome-perf-non-public',
    'ingest_folder': 'ingest',
    'commit_number': True,
    'revision_param': 'revision',
  },
  'webrtc': {
    'masters': ['WebRTCPerf'],
    'public_bucket_name': 'webrtc-perf-public',
    'internal_bucket_name': None,
    'ingest_folder': 'ingest-cp',
    'commit_number': True,
    'revision_param': 'revision',
  },
  'widevine-cdm': {
    'masters': ['WidevineCdmPerf'],
    'public_bucket_name': None,
    'internal_bucket_name': 'widevine-cdm-perf',
    'ingest_folder': 'ingest',
    'commit_number': False,
    'revision_param': 'r_cdm_git',
  },
  'widevine-whitebox': {
    'masters': ['WidevineWhiteboxPerf_master'],
    'public_bucket_name': None,
    'internal_bucket_name': 'widevine-whitebox-perf',
    'ingest_folder': 'ingest',
    'commit_number': False,
    'revision_param': 'r_cdm_git',
  },
  'v8': {
    'masters': ['internal.client.v8', 'client.v8'],
    'public_bucket_name': None,
    'internal_bucket_name': 'v8-perf-prod',
    'ingest_folder': 'ingest',
    'commit_number': True,
    'revision_param': 'revision',
  },
  'devtools-frontend': {
    'masters': ['client.devtools-frontend.integration'],
    'public_bucket_name': None,
    'internal_bucket_name': 'devtools-frontend-perf',
    'ingest_folder': 'ingest',
    'commit_number': False,
    'revision_param': 'r_devtools_git',
  }
}

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
  merge_errors = Metrics.counter('main', 'merge_errors')
  merged_rows = Metrics.counter('main', 'merged_rows')
  public_writes = Metrics.counter('main', 'public_writes')
  non_public_writes = Metrics.counter('main', 'non_public_writes')
  converted_rows = Metrics.counter('main', 'converted_rows')
  empty_bot_ids = Metrics.counter('main', 'empty_bot_ids')

  def HasMasters(row):
    repo_to_export = export_options.repo_to_export
    test_parts = row.key.parent.name.split('/')
    has_right_master = False
    for repo, props in REPOSITORY_PROPERTY_MAP.items():
      if repo_to_export == 'all' or repo_to_export == repo:
        has_right_master = test_parts[0] in props['masters']
        if has_right_master:
          break
    return has_right_master

  def RowEntityToDict(entity):
    row_entities_read.inc()
    try:
      d = {
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
      for repo, props in REPOSITORY_PROPERTY_MAP.items():
        if d['master_name'] in props['masters']:
          d['revision'] = entity.get(props['revision_param'])
          d['repo'] = repo
          break
      return [d]
    except KeyError:
      logging.getLogger().exception('Failed to convert Row')
      failed_row_entity_transforms.inc()
      return []

  time_range_provider = export_options.GetTimeRangeProvider()

  row_query_params = dict(project=project, kind='Row')
  row_dicts = (
      p
      | 'ReadFromDatastore(Row)' >> ReadTimestampRangeFromDatastore(
          row_query_params,
          time_range_provider=time_range_provider,
          step=datetime.timedelta(minutes=5))
      | 'Filter Non-Repo Rows' >> beam.Filter(HasMasters)
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

  masters_to_filter = []
  for repo, props in REPOSITORY_PROPERTY_MAP.items():
    if export_options.repo_to_export == 'all' or export_options.repo_to_export == repo: 
      masters_to_filter += props['masters']

  master_filter = [('master_name', 'IN', masters_to_filter)]
  test_metadata_dicts = (
      p
      | 'ReadFromDatastore(TestMetadata)' >> ReadFromDatastore(
          Query(project=project, kind='TestMetadata', filters=master_filter))
      |
      'ConvertEntityToDict(TestMetadata)' >> FlatMap(TestMetadataEntityToDict))

  def MergeRowAndTestMetadata(element):
    group_key, join_values = element
    rows, tests = join_values
    if len(tests) == 0:
      merge_errors.inc()
      logging.getLogger().exception('No TestMetadata for test (%s)', group_key)
      return []
    if len(tests) > 1:
      merge_errors.inc()
      logging.getLogger().exception('Multiple TestMetadata for test (%s)',
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
    return (row['master_name'], row['bot_name'], row['suite_name'], row['revision'],
      row['a_bot_id'], row['internal_only'], row['timestamp'], row['repo'])

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
        'revision': key[3],
        'bot_id': key[4],
        'internal_only': key[5],
        'timestamp': key[6],
    }
    repo = key[7]
    uses_commit_number = REPOSITORY_PROPERTY_MAP[repo]['commit_number']
    return [{
        'skia_data': ConvertRowsToSkiaPerf(
            rows,
            master=key_dict['master'],
            bot=key_dict['bot'],
            benchmark=key_dict['benchmark'],
            revision=key_dict['revision'],
            uses_commit_number=uses_commit_number,
        ),
        'key_dict': key_dict,
        'repo': repo,
    }]

  class WriteSkiaPerfBucket(beam.DoFn):

    def process(self, element): # pylint: disable=invalid-name
      key = element['key_dict']
      skia_data = element['skia_data']
      repo = element['repo']
      properties = REPOSITORY_PROPERTY_MAP[repo]
      public_bucket_name = properties['public_bucket_name']
      internal_bucket_name = properties['internal_bucket_name']


      is_internal = key['internal_only'] and key['master'] != 'WebRTCPerf'
      random_suffix = ''.join(random.choices(string.ascii_letters, k=10))
      gcs_suffix = '%s/%s/%s/%s/%s/%s-%s.json' % (
          properties['ingest_folder'],
          key['timestamp'],
          key['master'],
          key['bot'],
          key['benchmark'],
          '-'.join([str(key['revision']), key['bot_id']]),
          random_suffix)

      testing_mode = export_options.testing.get() != 'no'
      if not testing_mode:
        if not is_internal and public_bucket_name:
          filename = 'gs://%s/%s' % (public_bucket_name, gcs_suffix)
          with GcsIO().open(
              filename, mode='w', mime_type='application/json') as file:
            file.write(json.dumps(skia_data).encode('utf-8'))
            public_writes.inc()
        if internal_bucket_name:
          filename = 'gs://%s/%s' % (internal_bucket_name, gcs_suffix)
          with GcsIO().open(
              filename, mode='w', mime_type='application/json') as file:
            file.write(json.dumps(skia_data).encode('utf-8'))
            non_public_writes.inc()
      else:
        if not is_internal and public_bucket_name:
          logging.getLogger().info(public_bucket_name, gcs_suffix)
          public_writes.inc()
        if internal_bucket_name:
          non_public_writes.inc()
          logging.getLogger().info(internal_bucket_name, gcs_suffix)
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
