# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re

def ConvertRowsToSkiaPerf(rows, master, bot, benchmark, revision, uses_commit_number):
  """
  Converts a Row dicts into Skia Perf format and uploads it to Chromeperf GCS
  Bucket.

  Documentation on the Skia Perf format can be found here:
  https://skia.googlesource.com/buildbot/+/refs/heads/main/perf/FORMAT.md

  If the Rows are from an internal test, it's uploaded to the
  'chrome-perf-non-public' public. Otherwise, it's uploaded to the
  'chrome-perf-public' bucket.

  Say the input are Rows on commit position 12345 with the following public test format:
  'ChromiumAndroid/android-cronet-arm-rel/resource_sizes (CronetSample.apk)/*'.

  They'll be uploaded as a single file to the following example path:
  'gs://chrome-perf-public/ingest/2023/04/11/16/ChromiumAndroid/android-cronet-arm-rel/
  resource_sizes (CronetSample.apk)/12345.json'
  """

  skia_data = {
      'version': 1,
      'git_hash': 'CP:%s' % revision if uses_commit_number else revision,
      'key': {
          'master': master,
          'bot': bot,
          'benchmark': benchmark,
      },
      'results': [{
          'measurements': {
              'stat': _GetStatsForRow(row)
          },
          'key': _GetMeasurementKey(row)
      } for row in rows],
      'links': _GetLinks(rows[0])
  }

  return skia_data


def _GetStatsForRow(row):
  stats = []
  stats_key_map = [
      ('value', 'value'),
      ('error', 'error'),
      ('d_count', 'count'),
      ('d_max', 'max'),
      ('d_min', 'min'),
      ('d_sum', 'sum'),
      ('d_std', 'std'),
      ('d_avg', 'avg')
  ]

  for key, skia_key in stats_key_map:
    if key in row.keys() and _IsNumber(row[key]):
      stats.append({'value': skia_key, 'measurement': row[key]})

  return stats


def _GetMeasurementKey(row):
  measurement_key = {}

  measurement_key['improvement_direction'] = _GetImprovementDirection(
      row['improvement_direction'])

  measurement_key['unit'] = row['units']

  parts = row['test'].split('/')

  key_map = [
      'test',
      'subtest_1',
      'subtest_2',
      'subtest_3',
      'subtest_4',
      'subtest_5',
      'subtest_6',
      'subtest_7',
  ]
  if len(parts) >= 4:
    for i in range(3, len(parts)):
      if parts[i]:
        measurement_key[key_map[i-3]] = parts[i]
      else:
        break
  return measurement_key


def _GetLinks(row):
  links = {}
  annotations = [('Benchmark Config', 'a_benchmark_config'),
                 ('Tracing uri', 'a_tracing_uri'),
                 ('Test stdio', 'a_stdio_uri'),
                 ('Swarming Job Name', 'a_jobname')]

  if 'a_build_uri' in row.keys():
    build_page = row['a_build_uri']
    m = re.search(r'\[Build Status\]\((.+?)\)', build_page)
    if m:
      links['Build Page'] = m.group(1)
    else:
      links['Build Page'] = build_page

  if 'a_os_detail_vers' in row.keys():
    links['OS Version'] = ','.join(row['a_os_detail_vers'])

  if 'a_bot_id' in row.keys() and row['a_bot_id']:
    links['Bot Id'] = ', '.join(row['a_bot_id'].split(','))

  for name, annotation in annotations:
    if annotation in row.keys() and row[annotation]:
      links[name] = str(row[annotation])

  if 'r_commit_pos' in row.keys() and row['r_commit_pos']:
    links['Chromium Commit Position'] = 'https://crrev.com/%s' % row[
        'r_commit_pos']
  if 'r_chromium' in row.keys() and row['r_chromium']:
    links['Chromium Git Hash'] = (
        'https://chromium.googlesource.com/chromium/src/+/%s' %
        row['r_chromium'])
  if 'r_v8_rev' in row.keys() and row['r_v8_rev']:
    links['V8 Git Hash'] = 'https://chromium.googlesource.com/v8/v8/+/%s' % row[
        'r_v8_rev']
  if 'r_v8_git' in row.keys() and row['r_v8_git']:
    links['V8 Git Hash'] = 'https://chromium.googlesource.com/v8/v8/+/%s' % row[
        'r_v8_git']
  if 'r_webrtc_git' in row.keys() and row['r_webrtc_git']:
    links['WebRTC Git Hash'] = 'https://webrtc.googlesource.com/src/+/%s' % row[
        'r_webrtc_git']
  if 'r_chrome_version' in row.keys() and row['r_chrome_revision']:
    links['Chrome Version'] = (
        'https://chromium.googlesource.com/chromium/src/+/%s' %
        row['r_chrome_revision'])
  if 'r_devtools_git' in row.keys() and row['r_devtools_git']:
    links['Devtools Frontend Git Hash'] = (
      'https://chromium.googlesource.com/devtools/devtools-frontend/+/%s' %
        row['r_devtools_git'])

  return links


def _GetImprovementDirection(v):

  anomaly_directions = {0: 'up', 1: 'down', 4: 'unknown'}

  return anomaly_directions[v]


def _IsNumber(v):
  return isinstance(v, (float, int))
