# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import logging

from dashboard.pinpoint import test
from dashboard.pinpoint.models import change as change_module
from dashboard.pinpoint.models import job as job_module
from dashboard.pinpoint.models import task as task_module
from dashboard.pinpoint.models import evaluators
from dashboard.pinpoint.models import event as event_module
from dashboard.pinpoint.models.tasks import performance_bisection
from dashboard.pinpoint.models.tasks import read_value


class EvaluatorTest(test.TestCase):

  def setUp(self):
    super(EvaluatorTest, self).setUp()
    self.maxDiff = None
    self.job = job_module.Job.New((), ())

  def PopulateTaskGraph(self):
    task_module.PopulateTaskGraph(
        self.job,
        performance_bisection.CreateGraph(
            performance_bisection.TaskOptions(
                build_option_template=performance_bisection.BuildOptionTemplate(
                    builder='Some Builder',
                    target='performance_telemetry_test',
                    bucket='luci.bucket'),
                test_option_template=performance_bisection.TestOptionTemplate(
                    swarming_server='some_server',
                    dimensions=[],
                    extra_args=[],
                ),
                read_option_template=performance_bisection.ReadOptionTemplate(
                    benchmark='some_benchmark',
                    histogram_options=read_value.HistogramOptions(
                        tir_label='some_tir_label',
                        story='some_story',
                        statistic='avg',
                    ),
                    graph_json_options=read_value.GraphJsonOptions(
                        chart='some_chart',
                        trace='some_trace',
                    ),
                    mode='histogram_sets'),
                analysis_options=performance_bisection.AnalysisOptions(
                    comparison_magnitude=1.0,
                    min_attempts=10,
                    max_attempts=100,
                ),
                start_change=change_module.Change.FromDict({
                    'commits': [{
                        'repository': 'chromium',
                        'git_hash': 'commit_0'
                    }]
                }),
                end_change=change_module.Change.FromDict({
                    'commits': [{
                        'repository': 'chromium',
                        'git_hash': 'commit_5'
                    }]
                }),
                pinned_change=None,
            )))

  def testPopulateWorks(self):
    self.PopulateTaskGraph()

  def testEvaluateSuccess_NoReproduction(self):
    self.PopulateTaskGraph()
    task_module.Evaluate(
        self.job,
        event_module.Event(type='initiate', target_task=None, payload={}),
        evaluators.SequenceEvaluator([
            evaluators.FilteringEvaluator(
                predicate=evaluators.All(
                    evaluators.TaskTypeEq('read_value'),
                    evaluators.TaskStatusIn({'pending'})),
                delegate=evaluators.SequenceEvaluator([
                    FakeReadValueSameResult(self.job, 1.0),
                    evaluators.TaskPayloadLiftingEvaluator()
                ])),
            evaluators.SequenceEvaluator([
                performance_bisection.Evaluator(self.job),
                evaluators.TaskPayloadLiftingEvaluator(exclude_keys={'commits'})
            ]),
        ]))
    evaluate_result = task_module.Evaluate(
        self.job,
        event_module.Event(type='select', target_task=None, payload={}),
        evaluators.Selector(task_type='find_culprit'))
    self.assertIn('performance_bisection', evaluate_result)
    logging.info('Results: %s', evaluate_result['performance_bisection'])
    self.assertEquals(evaluate_result['performance_bisection']['culprits'], [])

  def testEvaluateSuccess_SpeculateBisection(self):
    self.skipTest('Implement this!')

  def testEvaluateSuccess_NeedToRefineAttempts(self):
    self.skipTest('Implement this!')

  def testEvaluateFailure_DependenciesFailed(self):
    self.skipTest('Implement this!')

  def testEvaluateFailure_DependenciesNoResults(self):
    self.skipTest('Implement this!')


class FakeReadValueSameResult(
    collections.namedtuple('FakeReadValueSameResult', (
        'job',
        'result',
    ))):
  __slots__ = ()

  def __call__(self, task, *_):
    task.payload.update({'result_values': [self.result]})
    return [
        lambda _: task_module.UpdateTask(
            self.job, task.id, new_state='completed', payload=task.payload)
    ]
