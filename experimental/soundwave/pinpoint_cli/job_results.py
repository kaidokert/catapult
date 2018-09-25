# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import csv
import posixpath

from pinpoint_cli import histograms_df
from services import isolate_service


def ChangeToStr(change):
  """Turn a pinpoint change dict into a string id."""
  change_id = ','.join(
      '{repository}@{git_hash}'.format(**commit)
      for commit in change['commits'])
  if 'patch' in change:
    change_id += '+' + change['patch']['url']
  return change_id


def IterTestOutputIsolates(job):
  """Iterate over test execution results for all changes tested in the job.

  Args:
    job: A pinpoint job dict with state.

  Yields:
    (change_id, isolate_hash) pairs for each completed test execution found in
    the job.
  """
  quests = job['quests']
  for change_state in job['state']:
    change_id = ChangeToStr(change_state['change'])
    for attempt in change_state['attempts']:
      executions = dict(zip(quests, attempt['executions']))
      if 'Test' not in executions:
        continue
      test_run = executions['Test']
      if not test_run['completed']:
        continue
      isolate_hash = next(
          d['value'] for d in test_run['details'] if d['key'] == 'isolate')
      yield change_id, isolate_hash


def DownloadResultsToCsv(job, output_file):
  results_file = posixpath.join(
      job['arguments']['benchmark'], 'perf_results.json')
  with open(output_file, 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(('change', 'isolate') + histograms_df.COLUMNS)
    num_rows = 0
    for change_id, isolate_hash in IterTestOutputIsolates(job):
      print 'Downloading results from isolate: %s ...' % isolate_hash
      files = isolate_service.RetrieveJson(isolate_hash, results_file)
      histograms_dict = isolate_service.RetrieveJson(
          files['files'][results_file]['h'], results_file)
      for row in histograms_df.IterRows(histograms_dict):
        row = (change_id, isolate_hash) + row
        writer.writerow(row)
        num_rows += 1
  print 'Wrote data from %s histograms in %s.' % (num_rows, output_file)
