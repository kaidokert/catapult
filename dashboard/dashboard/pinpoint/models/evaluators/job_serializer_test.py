# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import mock
import logging

from dashboard.pinpoint.models import evaluators
from dashboard.pinpoint.models import job as job_module
from dashboard.pinpoint.models import task as task_module
from dashboard.pinpoint.models.tasks import bisection_test
from dashboard.pinpoint.models.tasks import performance_bisection


@mock.patch.object(job_module.results2, 'GetCachedResults2',
                   mock.MagicMock(return_value='http://foo'))
class EvaluatorTest(bisection_test.BisectionTestBase):

  def setUp(self):
    super(EvaluatorTest, self).setUp()
    self.maxDiff = None
    self.job = job_module.Job.New((), (), use_execution_engine=True)

  def testSerializeJob(self):
    self.PopulateSimpleBisectionGraph(self.job)
    _ = task_module.Evaluate(
        self.job, bisection_test.SelectEvent(),
        evaluators.DispatchByTaskType({
            'find_isolate': bisection_test.FakeFoundIsolate(self.job),
            'run_test': bisection_test.FakeSuccessfulRunTest(self.job),
            'read_value': bisection_test.FakeReadValueSameResult(self.job, 1.0),
            'find_culprit': performance_bisection.Evaluator(self.job),
        }))
    logging.debug('Finished evaluating job state.')
    job_dict = self.job.AsDict(options=[job_module.OPTION_STATE])
    self.assertTrue(self.job.use_execution_engine)
    self.assertEqual(
        {
            'arguments': {},
            'bug_id':
                None,
            'cancel_reason':
                None,
            'comparison_mode':
                None,
            'configuration':
                None,
            'created':
                mock.ANY,
            'difference_count':
                None,
            'exception':
                None,
            'job_id':
                mock.ANY,
            'name':
                mock.ANY,
            'quests': ['Build'],
            'results_url':
                mock.ANY,
            'status':
                mock.ANY,
            'updated':
                mock.ANY,
            'user':
                None,
            'state': [{
                'attempts': [{
                    'executions': [{
                        'completed': True,
                        'exception': None,
                        'details': mock.ANY,
                    }]
                }],
                'change': mock.ANY,
            }, {
                'attempts': [{
                    'executions': [{
                        'completed': True,
                        'exception': None,
                        'details': mock.ANY,
                    }]
                }],
                'change': mock.ANY,
            }]
        }, job_dict)
