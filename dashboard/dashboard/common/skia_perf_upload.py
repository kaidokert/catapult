# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import datetime
import json
import logging
import time

try:
  import cloudstorage.cloudstorage as cloudstorage
except ImportError:
  # This is a work around to fix the discrepency on file tree in tests.
  import cloudstorage

from dashboard.common import utils

PUBLIC_BUCKET_NAME = 'chrome-perf-public'
INTERNAL_BUCKET_NAME = 'chrome-perf-non-public'


def UploadRow(row):
  """
  Converts a Row entity into Skia Perf format and uploads it to Chromeperf GCS
  Bucket.

  Documentation on the Skia Perf format can be found here:
  https://skia.googlesource.com/buildbot/+/refs/heads/main/perf/FORMAT.md

  If the Row is from an internal test, it's uploaded to the
  'chrome-perf-non-public' public. Otherwise, it's uploaded to the
  'chrome-perf-public' bucket.

  Take for example a Row on the following public test:
  'ChromiumAndroid/android-cronet-arm-rel/resource_sizes (CronetSample.apk)/InstallSize/APK size'.

  It'll be uploaded to the following example path:
  'gs://chrome-perf-public/perf/2023/04/11/16/ChromiumAndroid/android-cronet-arm-rel/resource_sizes (CronetSample.apk)/InstallSize/APK size//1681231603.3381824.json'

  Args:
    row: A Row entity.
  """

  # Currently, we only support rows with a Chromium commit position, as it's
  # the only format our Skia Perf instance can support.
  if not hasattr(row, 'r_commit_pos'):
    raise RuntimeError('Row has no Chromium commit position')

  test_path = utils.TestPath(row.parent_test)
  test_key = utils.TestKey(test_path)
  test = test_key.get()

  skia_data = _ConvertRowToSkiaPerf(row, test)

  internal_only = test.internal_only

  bucket_name = INTERNAL_BUCKET_NAME if internal_only else PUBLIC_BUCKET_NAME

  filename = '%s/%s/%s.json' % (test_path, str(row.r_commit_pos), time.time())
  filename = '/%s/perf/%s/%s' % (
      bucket_name, datetime.datetime.now().strftime('%Y/%m/%d/%H'), filename)

  gcs_file = cloudstorage.open(
      filename,
      'w',
      content_type='application/json',
      retry_params=cloudstorage.RetryParams(backoff_factor=1.1))

  gcs_file.write(json.dumps(skia_data))

  logging.info('Uploaded row to %s' % filename)

  gcs_file.close()


def _ConvertRowToSkiaPerf(row, test):

  commit_position = row.r_commit_pos

  skia_data = {
      'version': 1,
      'git_hash': 'CP:%s' % str(commit_position),
      'key': {
          'master': test.master_name,
          'bot': test.bot_name,
          'benchmark': test.suite_name,
      },
      'results': [{
          'measurements': {
              'stat': _GetStatsForRow(row)
          },
          'key': _GetMeasurementKey(test)
      }],
      'links': _GetLinks(row)
  }

  return skia_data


def _GetStatsForRow(row):
  stats = []
  stats.append({'value': 'value', 'measurement': row.value})
  stats.append({'value': 'error', 'measurement': row.error})

  if hasattr(row, 'd_count'):
    stats.append({'value': 'count', 'measurement': row.d_count})
  if hasattr(row, 'd_max'):
    stats.append({'value': 'max', 'measurement': row.d_max})
  if hasattr(row, 'd_min'):
    stats.append({'value': 'min', 'measurement': row.d_min})
  if hasattr(row, 'd_sum'):
    stats.append({'value': 'sum', 'measurement': row.d_sum})
  if hasattr(row, 'd_std'):
    stats.append({'value': 'std', 'measurement': row.d_std})
  if hasattr(row, 'd_avg'):
    stats.append({'value': 'avg', 'measurement': row.d_avg})

  return stats


def _GetMeasurementKey(test):
  return {
      'unit': test.units,
      'improvement_direction': test.improvement_direction,
      'subtest_1': test.test_part1_name,
      'subtest_2': test.test_part2_name,
      'subtest_3': test.test_part3_name,
      'subtest_4': test.test_part4_name,
      'subtest_5': test.test_part5_name,
  }


def _GetLinks(row):
  links = {}

  # Annotations
  if hasattr(row, 'a_benchmark_config'):
    links['Benchmark Config'] = row.a_benchmark_config
  if hasattr(row, 'a_build_uri'):
    links['Build Page'] = row.a_build_uri
  if hasattr(row, 'a_tracing_uri'):
    links['Tracing uri'] = row.a_tracing_uri
  if hasattr(row, 'a_stdio_uri'):
    links['Test stdio'] = row.a_stdio_uri
  if hasattr(row, 'a_bot_id'):
    links['Test bot'] = row.a_bot_id
  if hasattr(row, 'a_os_detail_vers'):
    links['OS Version'] = row.a_os_detail_vers
  if hasattr(row, 'a_default_rev'):
    links['Default Revision'] = row.a_default_rev
  if hasattr(row, 'a_jobname'):
    links['Swarming Job Name'] = row.a_jobname

  # Revisions
  if hasattr(row, 'r_commit_pos'):
    links['Chromium Commit Position'] = row.r_commit_pos
  if hasattr(row, 'r_chromium'):
    links['Chromium Git Hash'] = row.r_chromium
  if hasattr(row, 'r_v8_rev'):
    links['V8 Git Hash'] = row.r_v8_rev
  if hasattr(row, 'r_webrtc_git'):
    links['WebRTC Git Hash'] = row.r_webrtc_git
  if hasattr(row, 'r_chrome_version'):
    links['Chrome Version'] = row.r_chrome_version
  if hasattr(row, 'r_cros_version'):
    links['ChromeOS Version'] = row.r_cros_version

  return links
