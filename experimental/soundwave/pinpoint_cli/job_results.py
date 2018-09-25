# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


def CommitToStr(commit):
  """Turn a pinpoint commit dict into a string id."""
  return '@'.join([commit['repository'], commit['git_hash']])


def ChangeToStr(change):
  """Turn a pinpoint change dict into a string id."""
  change_id = ','.join(CommitToStr(c) for c in change['commits'])
  if 'patch' in change:
    change_id = '+'.join([change_id, change['patch']['url']])
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
