# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Pinpoint Bisection Sandwich Results Update Handler

This HTTP handler is responsible for polling the state of the various FIFO
queues currently defined in the service, and running queued jobs as they are
ready. The scheduler enforces that there's only one currently runing job for any
configuration, and does not attempt to do any admission control nor load
shedding. Those features will be implemented in a dedicated scheduler service.
"""

from flask import make_response

from dashboard.pinpoint.models import sandwich_workflow_group

def SandwichResultsUpdateHandler():
  _GetWorkflowGroup()
  _UpdateVerificationResults(sandwich_workflow_group.SandwichWorkflowGroup)
  return make_response('', 200)


def _GetWorkflowGroup() -> [sandwich_workflow_group.SandwichWorkflowGroup]:
  pass


def _UpdateVerificationResults(sandwich_workflow_group.SandwichWorkflowGroup):
  # Calculate issue metadata
  _CalculateIssueMetadata(sandwich_workflow_group.SandwichWorkflowGroup)
  # Summarize verification results
  _SummarizeResults(...)
  # # culprits we were able to verify as regressions,
  # # culprits failed sandwich verification, 
  # # culprits were not real regressions
  _UpdateAndMergeBug(...)
  pass

def _CalculateIssueMetadata(sandwich_workflow_group.SandwichWorkflowGroup):
  pass