# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import logging

from google.cloud.workflows import executions_v1
from google.cloud.workflows.executions_v1.types import executions

PROJECT = 'chromeperf'
LOCATION = 'us-central1'
WORKFLOW_NAME = 'sandwich-verification-workflow-prod'


class SandwichVerificationWorkflow:

  def __init__(self,
               project=PROJECT,
               location=LOCATION,
               workflow=WORKFLOW_NAME):
    # Set up API clients.
    self.execution_client = executions_v1.ExecutionsClient()

    # Construct the fully qualified location path.
    self.parent = self.execution_client.workflow_path(project, location,
                                                      workflow)

  def CreateExecution(self, anomaly):
    arguments = {'anomaly': anomaly}

    execution = executions.Execution(argument=json.dumps(arguments))
    response = self.execution_client.create_execution(
        parent=self.parent, execution=execution)
    logging.info('Created Alert Group Verification execution: %s.',
                 response.name)
    return response.name

  def GetExecution(self, execution_name):

    request = executions_v1.GetExecutionRequest(name=execution_name)
    response = self.execution_client.get_execution(request=request)

    # Execution object.
    return response
