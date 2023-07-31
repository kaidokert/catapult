# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Tests the culprit verification results update Handler."""

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import mock
import json

from dashboard.common import testing_common
from dashboard.pinpoint import test
from dashboard.pinpoint.handlers import culprit
from dashboard.pinpoint.models import job_bug_update
from dashboard.pinpoint.models import sandwich_workflow_group
from dashboard.services import perf_issue_service_client
from dashboard.services import workflow_service
from google.appengine.ext import ndb


class FakeResponse():

  def __init__(self, state, result):
    self.state = state
    self.result = result


class CulpritTest(test.TestCase):

  @mock.patch(
      'dashboard.pinpoint.models.sandwich_workflow_group.SandwichWorkflowGroup.GetAll',
      mock.MagicMock(return_value=[
          sandwich_workflow_group.SandwichWorkflowGroup(
              metric='test_metric', url='test_url', cloud_workflows_keys=[1])
      ]))
  @mock.patch(
      'dashboard.services.workflow_service.GetExecution',
      mock.MagicMock(
          return_value=FakeResponse(workflow_service.EXECUTION_STATE_SUCCEEDED,
                                    json.dumps({'decision': False}))))
  @mock.patch('dashboard.services.perf_issue_service_client.PostIssueComment',
              mock.MagicMock())
  @mock.patch(
      'dashboard.pinpoint.models.job_bug_update.DifferencesFoundBugUpdateBuilder',
      mock.MagicMock())
  def testCulpritVerificationAllExecutionCompletedZeroVerified(self):
    sandwich_workflow_group.CloudWorkflow(
        key=ndb.Key('CloudWorkflow', 1), execution_name='execution-id-0').put()
    response = self.testapp.get('/cron/update-culprit-verification-results')
    self.assertEqual(response.status_code, 200)

  @mock.patch(
      'dashboard.pinpoint.models.sandwich_workflow_group.SandwichWorkflowGroup.GetAll',
      mock.MagicMock(return_value=[
          sandwich_workflow_group.SandwichWorkflowGroup(
              metric='test_metric', cloud_workflows_keys=[1])
      ]))
  @mock.patch('dashboard.services.workflow_service.GetExecution',
              mock.MagicMock())
  @mock.patch('dashboard.services.perf_issue_service_client.PostIssueComment',
              mock.MagicMock())
  def testCulpritVerificationAllExecutionCompletedNonZeroVerified(self):
    sandwich_workflow_group.CloudWorkflow(
        key=ndb.Key('CloudWorkflow', 1),
        execution_name='test_execution_name').put()
    response = self.testapp.get('/cron/update-culprit-verification-results')
    self.assertEqual(response.status_code, 200)

  @mock.patch(
      'dashboard.pinpoint.models.sandwich_workflow_group.SandwichWorkflowGroup.GetAll',
      mock.MagicMock(return_value=[]))
  def testCulpritVerificationNoExecutionExisted(self):
    response = self.testapp.get('/cron/update-culprit-verification-results')
    self.assertEqual(response.status_code, 200)
