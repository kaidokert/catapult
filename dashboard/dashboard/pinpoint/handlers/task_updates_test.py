# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import base64
import json
import logging
import mock
import sys

from dashboard.pinpoint import test
from dashboard.pinpoint.models import job as job_module
from dashboard.pinpoint.models.tasks import bisection_test_util


class TaskUpdatesTest(test.TestCase):

  def setUp(self):
    # Intercept the logging messages, so that we can see them when we have test
    # output in failures.
    self.logger = logging.getLogger()
    self.logger.level = logging.DEBUG
    self.stream_handler = logging.StreamHandler(sys.stdout)
    self.logger.addHandler(self.stream_handler)
    self.addCleanup(self.logger.removeHandler, self.stream_handler)
    super(TaskUpdatesTest, self).setUp()

  def testPostWorks(self):
    self.Post(
        '/_ah/push-handlers/task-updates',
        json.dumps({
            'message': {
                'attributes': {
                    'key': 'value'
                },
                'data':
                    base64.urlsafe_b64encode(
                        json.dumps({
                            'task_id':
                                'some_id',
                            'userdata':
                                json.dumps({
                                    'job_id': 'cafef00d',
                                    'task': {
                                        'id': 1,
                                        'type': 'build',
                                    }
                                }),
                        }))
            }
        }),
        status=204)

  def testPostInvalidData(self):
    self.Post(
        '/_ah/push-handlers/task-updates',
        json.dumps({
            'message': {
                'attributes': {
                    'nothing': 'important'
                },
                'data': '{"not": "base64-encoded"}',
            },
        }),
        status=204)
    self.Post(
        '/_ah/push-handlers/task-updates',
        json.dumps({
            'message': {
                'attributes': {
                    'nothing': 'important'
                },
                'data': base64.urlsafe_b64encode('not json formatted'),
            },
        }),
        status=204)


@mock.patch('dashboard.common.utils.ServiceAccountHttp', mock.MagicMock())
@mock.patch('dashboard.services.buildbucket_service.Put')
@mock.patch('dashboard.services.buildbucket_service.GetJobStatus')
class ExecutionEngineTaskUpdatesTest(bisection_test_util.BisectionTestBase):

  def testExecutionEngineJobUpdates(self, buildbucket_put,
                                    buildbucket_getjobstatus):
    buildbucket_put.return_value = {'build': {'id': '92384098123'}}
    buildbucket_getjobstatus.return_value = {
        'build': {
            'status':
                'COMPLETED',
            'result':
                'SUCCESS',
            'result_details_json':
                """
            {
              "properties": {
                "got_revision_cp": "refs/heads/master@commit_0",
                "isolate_server": "https://isolate.server",
                "swarm_hashes_refs/heads/master(at)commit_0_without_patch":
                  {"performance_telemetry_test": "1283497aaf223e0093"}
              }
            }
            """
        }
    }

    job = job_module.Job.New((), (), use_execution_engine=True)
    self.PopulateSimpleBisectionGraph(job)
    self.assertTrue(job.use_execution_engine)
    job.Start()
    self.Post(
        '/_ah/push-handlers/task-updates',
        json.dumps({
            'message': {
                'attributes': {
                    'nothing': 'important',
                },
                'data':
                    base64.urlsafe_b64encode(
                        json.dumps({
                            'task_id':
                                'some_task_id',
                            'userdata':
                                json.dumps({
                                    'job_id': job.job_id,
                                    'task': {
                                        'type': 'build',
                                        'id': 'find_isolate@commit_0'
                                    }
                                })
                        }))
            }
        }),
        status=204)
