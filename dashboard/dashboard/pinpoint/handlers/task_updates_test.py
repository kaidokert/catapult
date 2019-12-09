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


def FailsWithKeyError(*_):
  raise KeyError('Mock failure')


@mock.patch('dashboard.common.utils.ServiceAccountHttp', mock.MagicMock())
@mock.patch('dashboard.services.buildbucket_service.Put')
@mock.patch('dashboard.services.buildbucket_service.GetJobStatus')
class ExecutionEngineTaskUpdatesTest(bisection_test_util.BisectionTestBase):

  def testHandlerGoodCase(self, *_):
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
                                        # Use an ID that's not real.
                                        'id': '1',
                                        'type': 'build',
                                    }
                                }),
                        }))
            }
        }))

  def testPostInvalidData(self, *_):
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

  @mock.patch(
      'dashboard.pinpoint.models.isolate.Get', side_effect=FailsWithKeyError)
  @mock.patch('dashboard.services.swarming.Tasks.New')
  def testExecutionEngineJobUpdates(self, swarming_tasks_new, isolate_get,
                                    buildbucket_getjobstatus, buildbucket_put):
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
    swarming_tasks_new.return_value = {'task_id': 'task id'}

    job = job_module.Job.New((), (), use_execution_engine=True)
    self.PopulateSimpleBisectionGraph(job)
    self.assertTrue(job.use_execution_engine)
    job.Start()

    # We are expecting two builds to be scheduled at the start of a bisection.
    self.assertEqual(2, isolate_get.call_count)
    self.assertEqual(2, buildbucket_put.call_count)

    # We expect no invocations of the job status.
    self.assertEqual(0, buildbucket_getjobstatus.call_count)

    # We then post an update and expect it to succeed.
    task_updates.HandleTaskUpdate(
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
                                        'id': 'find_isolate_chromium@commit_5'
                                    }
                                })
                        }))
            }
        }))

    # Here we expect one invocation of the getjobstatus call.
    self.assertEqual(1, buildbucket_getjobstatus.call_count)

    # And we expect that there's more than 1 call to the swarming service for
    # new tasks.
    self.assertGreater(swarming_tasks_new.call_count, 1)
