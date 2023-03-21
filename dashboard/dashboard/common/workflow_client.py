# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import logging

from google.cloud import workflows_v1beta
from google.cloud.workflows import executions_v1beta
from google.cloud.workflows.executions_v1beta.types import executions

PROJECT = 'chromeperf'
LOCATION = 'us-central1'

class SandwichVerificationWorkflow:

  def __init__(self, project=PROJECT, location=LOCATION):
    # Set up API clients.
    self.execution_client = executions_v1beta.ExecutionsClient()
    self.workflows_client = workflows_v1beta.WorkflowsClient()

    # Construct the fully qualified location path.
    self.parent = self.workflows_client.workflow_path(project, location, 'sandwich-verification-workflow')

  def ExecuteAlertGroupMode(self, anomaly, group_key, update):
    arguments = {
        'anomaly': anomaly,
        'mode': 'alert_group',
        'group_key': group_key,
        'update': update,
    }
    execution = executions.Execution(argument=json.dumps(arguments))
    response = self.execution_client.create_execution(parent=self.parent, execution=execution)
    logging.info('Created Alert Group Verification execution: %s.' % response.name)
    return response
