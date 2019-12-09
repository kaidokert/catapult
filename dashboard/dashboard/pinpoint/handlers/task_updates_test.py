# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import base64
import json
import mock

from dashboard.pinpoint.models import job as job_module
from dashboard.pinpoint.models.tasks import bisection_test_util
from dashboard.pinpoint.handlers import task_updates


class TaskUpdateHandlerTest(bisection_test_util.BisectionTestBase):

  def testHandlerGoodCase(self):
    job = job_module.Job.New((), (), use_execution_engine=True)
    self.PopulateSimpleBisectionGraph(job)
    task_updates.HandleTaskUpdate(
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
                                    'job_id': job.job_id,
                                    'task': {
                                        'id': 1,
                                        'type': 'build',
                                    }
                                }),
                        }))
            }
        }))

  def testPostInvalidData(self):
    with self.assertRaisesRegexp(ValueError, 'Failed decoding `data`'):
      task_updates.HandleTaskUpdate(
          json.dumps({
              'message': {
                  'attributes': {
                      'nothing': 'important'
                  },
                  'data': '{"not": "base64-encoded"}',
              },
          }))
    with self.assertRaisesRegexp(ValueError, 'Failed JSON parsing `data`'):
      task_updates.HandleTaskUpdate(
          json.dumps({
              'message': {
                  'attributes': {
                      'nothing': 'important'
                  },
                  'data': base64.urlsafe_b64encode('not json formatted'),
              },
          }))


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
