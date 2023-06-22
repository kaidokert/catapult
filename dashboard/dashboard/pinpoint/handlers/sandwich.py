# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Pinpoint Bisection Sandwich Results Update Handler

This HTTP handler is responsible for checking the state of the SandwichWorkflowGroup.
If all Workflow executions are finished, then update the sandwich verification results.
"""

import json
from flask import make_response

from google.appengine.api import taskqueue

from dashboard.common import workflow_client
from dashboard.pinpoint.models import job_bug_update
from dashboard.pinpoint.models import sandwich_workflow_group
from dashboard.services import perf_issue_service_client
from google.cloud.workflows.executions_v1.types import executions


_ROUND_PUSHPIN = u'\U0001f4cd'
RETRY_OPTIONS = taskqueue.TaskRetryOptions(
    task_retry_limit=8, min_backoff_seconds=2)


def SandwichResultsUpdateHandler():
  workflow_groups = sandwich_workflow_group.SandwichWorkflowGroup.GetAll()
  client = workflow_client.SandwichVerificationWorkflow()
  for group in workflow_groups:
    print(group)
    if _AllExecutionCompleted(group, client):
      bug_update_builder = job_bug_update.DifferencesFoundBugUpdateBuilder(group.metric)
      num_succeeded, num_failed, num_cancelled, num_invalid, num_verified = _SummarizeResults(group, client, bug_update_builder)
      num_workflows = len(group.workflows)
      if num_succeeded == num_workflows and num_verified == 0:
        # Close the bug and update the comment.
        title = "<b>Sandwich verification can't verify the culprit(s) found by Pinpoint job %s.</b>" % _ROUND_PUSHPIN
        deferred.defer(
          _PostBugCommentDeferred,
          group.bug_id,
          group.project,
          comment='\n'.join((title, group.url)),
          labels=job_bug_update.ComputeLabelUpdates(
            ['Sandwich-Verification-Completed', 'Sandwich-Verification-No-Repro']),
          status='WontFix',
          _retry_options=RETRY_OPTIONS)
      else:
        # Update and merge the bug
        # TODO: convert group.improvement_dir to the correct format
        deferred.defer(
            job_bug_update.UpdatePostAndMergeDeferred,
            bug_update_builder,
            group.bug_id,
            group.tags,
            group.url,
            group.project,
            group.improvement_dir,
            _retry_options=RETRY_OPTIONS)
      group.active = False
    group.put()
  return make_response('', 200)


def _AllExecutionCompleted(group, client):
  workflows = group.workflows
  completed = True
  for w in workflows:
    response = client.GetExecution(w.execution_name)
    if response.state == executions.Execution.State.SUCCEEDED:
      w.execution_status = 'SUCCEEDED'
    elif response.state == executions.Execution.State.FAILED:
      w.execution_status = 'FAILED'
    elif response.state == executions.Execution.State.CANCELLED:
      w.execution_status = 'CANCELLED'
    elif response.state == executions.Execution.State.STATE_UNSPECIFIED:
      w.execution_status = 'STATE_UNSPECIFIED'
    else:
      completed = False
  return completed


def _SummarizeResults(group, client, bug_update_builder):
  num_succeeded, num_failed, num_cancelled, num_invalid, num_verified = 0, 0, 0, 0, 0
  for w in workflows:
    response = client.GetExecution(w.execution_name)
    if response.state == executions.Execution.State.SUCCEEDED:
      num_succeeded += 1
      result_dict = json.loads(response.result)
      # TODO: double check that the following is in the right format.
      if result_dict['response'] and result_dict['response']['verification'] and result_dict['response']['verification']['decision']:
        decision = result_dict['response']['verification']['decision']
        if decision:
          # TODO: can we use w.commit_dict directly?
          bug_update_builder.AddDifference(None, w.values_a, w.values_b, w.kind, w.commit_dict)
          num_verified += 1
    elif response.state == executions.Execution.State.FAILED:
      bug_update_builder.AddDifference(None, w.values_a, w.values_b, w.kind, w.commit_dict)
      num_failed += 1
    elif response.state == executions.Execution.State.CANCELLED:
      bug_update_builder.AddDifference(None, w.values_a, w.values_b, w.kind, w.commit_dict)
      num_cancelled += 1
    elif response.state == executions.Execution.State.STATE_UNSPECIFIED:
      bug_update_builder.AddDifference(None, w.values_a, w.values_b, w.kind, w.commit_dict)
      num_invalid += 1
  return num_succeeded, num_failed, num_cancelled, num_invalid, num_verified


def _PostBugCommentDeferred(bug_id, *args, **kwargs):
  if not bug_id:
    return

  perf_issue_service_client.PostIssueComment(bug_id, *args, **kwargs)
