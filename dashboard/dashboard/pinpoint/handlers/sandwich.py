# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Pinpoint Bisection Sandwich Results Update Handler

This HTTP handler is responsible for checking the state of the SandwichWorkflowGroup.
If all Workflow executions are finished, then update the sandwich verification results.
"""

from flask import make_response

from dashboard.common import workflow_client
from dashboard.pinpoint.models import sandwich_workflow_group
from google.cloud.workflows.executions_v1.types import executions

def SandwichResultsUpdateHandler():
  workflow_groups = sandwich_workflow_group.SandwichWorkflowGroup.GetAll()
  for group in workflow_groups:
    print(group)
    if _AllExecutionCompleted(group):
      # Update sandwich verification results.
      # 1). Calculate issue metadata.
      _CalculateIssueMetadata(group)
      # 2). Summarize verification results
      _SummarizeResults(group)
      # 3). Update and merge bugs.
      _UpdateAndMergeBug(group)
      # Mark the SandwichWorkflowGroup inactive.
      group.active = False
    group.put()
  return make_response('', 200)


def _AllExecutionCompleted(group):
  workflows = group.workflows
  completed = True
  client = workflow_client.SandwichVerificationWorkflow()
  for w in workflows:
    response = client.GetExecution(w.execution_name)
    if response.state == executions.Execution.State.SUCCEEDED:
      w.execution_status = 'SUCCEEDED'
    elif response.state == executions.Execution.State.FAILED:
      w.execution_status = 'FAILED'
    elif response.state == executions.Execution.State.CANCELLED:
      w.execution_status = 'CANCELLED'
    else:
      completed = False
  return completed


def _CalculateIssueMetadata(group):
  pass


def _SummarizeResults(group):
  pass


def _UpdateAndMergeBug(group):
  # culprits we were able to verify as regressions,
  # culprits failed sandwich verification, 
  # culprits were not real regressions
  pass