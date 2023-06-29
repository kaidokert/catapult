# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Pinpoint Bisection Sandwich Verification Results Update Handler

This HTTP handler is responsible for checking the state of the
SandwichWorkflowGroup. If all Workflow executions are finished,
then update the sandwich verification results.
"""
from __future__ import absolute_import

import json
from flask import make_response

from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.api import taskqueue
from google.cloud.workflows.executions_v1.types import executions

from dashboard.common import workflow_client
from dashboard.models import anomaly
from dashboard.pinpoint.models import job_bug_update
from dashboard.pinpoint.models import sandwich_workflow_group
from dashboard.services import perf_issue_service_client


_ROUND_PUSHPIN = u'\U0001f4cd'
RETRY_OPTIONS = taskqueue.TaskRetryOptions(
    task_retry_limit=8, min_backoff_seconds=2)


def CulpritVerificationResultsUpdateHandler():
  workflow_groups = sandwich_workflow_group.SandwichWorkflowGroup.GetAll()
  client = workflow_client.SandwichVerificationWorkflow()
  for group in workflow_groups:
    if _AllExecutionCompleted(group, client):
      bug_update_builder = job_bug_update.DifferencesFoundBugUpdateBuilder(group.metric)
      num_succeeded, num_verified = _SummarizeResults(
        group.cloud_workflows_keys, client, bug_update_builder)
      num_workflows = len(group.workflows)
      if num_succeeded == num_workflows and num_verified == 0:
        # Close the bug and update the comment.
        title = ("<b>Sandwich verification can't verify the culprit(s) found by "
                 "Pinpoint job %s.</b>" % _ROUND_PUSHPIN)
        deferred.defer(
          _PostBugCommentDeferred,
          group.bug_id,
          group.project,
          comment='\n'.join((title, group.url)),
          labels=job_bug_update.ComputeLabelUpdates(
            ['Culprit-Verification-No-Repro']),
          status='WontFix',
          _retry_options=RETRY_OPTIONS)
      else:
        # Update and merge the bug
        improvement_dir = _GetImprovementDir(group.improvement_dir)
        deferred.defer(
            job_bug_update.UpdatePostAndMergeDeferred,
            bug_update_builder,
            group.bug_id,
            group.tags,
            group.url,
            group.project,
            improvement_dir,
            _retry_options=RETRY_OPTIONS)
      group.active = False
    group.put()
  return make_response('', 200)


def _AllExecutionCompleted(group, client):
  cloud_workflows_keys = group.cloud_workflows_keys
  completed = True
  for wk in cloud_workflows_keys:
    could_workflow = ndb.Key('CloudWorkflow', wk).get()
    response = client.GetExecution(could_workflow.execution_name)
    if response.state == executions.Execution.State.SUCCEEDED:
      could_workflow.execution_status = 'SUCCEEDED'
    elif response.state == executions.Execution.State.FAILED:
      could_workflow.execution_status = 'FAILED'
    elif response.state == executions.Execution.State.CANCELLED:
      could_workflow.execution_status = 'CANCELLED'
    elif response.state == executions.Execution.State.STATE_UNSPECIFIED:
      could_workflow.execution_status = 'STATE_UNSPECIFIED'
    else:
      completed = False
    could_workflow.put()
  return completed


def _SummarizeResults(cloud_workflows_keys, client, bug_update_builder):
  num_succeeded, num_verified = 0, 0
  for wk in cloud_workflows_keys:
    w = ndb.Key('CloudWorkflow', wk)
    response = client.GetExecution(w.execution_name)
    if response.state == executions.Execution.State.SUCCEEDED:
      num_succeeded += 1
      result_dict = json.loads(response.result)
      if result_dict['response'] and result_dict['response']['verification'] \
        and result_dict['response']['verification']['decision']:
        decision = result_dict['response']['verification']['decision']
        if decision:
          bug_update_builder.AddDifference(None, w.values_a, w.values_b, w.kind, w.commit_dict)
          num_verified += 1
    elif response.state in [executions.Execution.State.FAILED, executions.Execution.State.CANCELLED,
      executions.Execution.State.STATE_UNSPECIFIED]:
      bug_update_builder.AddDifference(None, w.values_a, w.values_b, w.kind, w.commit_dict)
  return num_succeeded, num_verified


def _PostBugCommentDeferred(bug_id, *args, **kwargs):
  if not bug_id:
    raise Exception('Post bug comment failed because bug id is missing')

  perf_issue_service_client.PostIssueComment(bug_id, *args, **kwargs)


def _GetImprovementDir(improvement_dir):
  if improvement_dir == 'UP':
    return anomaly.UP
  if improvement_dir == 'DOWN':
    return anomaly.DOWN
  return anomaly.UNKNOWN
