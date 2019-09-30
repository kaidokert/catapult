# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import functools
import itertools
import json
import mock
import unittest

from dashboard.pinpoint import test
from dashboard.pinpoint.models import change as change_module
from dashboard.pinpoint.models import evaluators
from dashboard.pinpoint.models import event as event_module
from dashboard.pinpoint.models import job as job_module
from dashboard.pinpoint.models import task as task_module
from dashboard.pinpoint.models.quest import find_isolate
from dashboard.pinpoint.models.quest import read_value
from dashboard.pinpoint.models.quest import run_test
from tracing.value import histogram as histogram_module
from tracing.value import histogram_set
from tracing.value.diagnostics import generic_set
from tracing.value.diagnostics import reserved_infos



_BASE_ARGUMENTS_HISTOGRAMS = {'benchmark': 'speedometer'}
_BASE_ARGUMENTS_GRAPH_JSON = {
    'benchmark': 'base_perftests',
    'chart': 'chart_name',
    'trace': 'trace_name',
}


class ReadHistogramsJsonValueQuestTest(unittest.TestCase):

  def testMinimumArguments(self):
    quest = read_value.ReadHistogramsJsonValue.FromDict(
        _BASE_ARGUMENTS_HISTOGRAMS)
    expected = read_value.ReadHistogramsJsonValue(
        'speedometer/perf_results.json')
    self.assertEqual(quest, expected)

  def testAllArguments(self):
    arguments = dict(_BASE_ARGUMENTS_HISTOGRAMS)
    arguments['chart'] = 'timeToFirst'
    arguments['tir_label'] = 'pcv1-cold'
    arguments['trace'] = 'trace_name'
    arguments['statistic'] = 'avg'
    quest = read_value.ReadHistogramsJsonValue.FromDict(arguments)

    expected = read_value.ReadHistogramsJsonValue(
        'speedometer/perf_results.json', 'timeToFirst',
        'pcv1-cold', 'trace_name', 'avg')
    self.assertEqual(quest, expected)

  def testWindows(self):
    arguments = dict(_BASE_ARGUMENTS_HISTOGRAMS)
    arguments['dimensions'] = [{'key': 'os', 'value': 'Windows-10'}]
    quest = read_value.ReadHistogramsJsonValue.FromDict(arguments)

    expected = read_value.ReadHistogramsJsonValue(
        'speedometer\\perf_results.json')
    self.assertEqual(quest, expected)


class ReadGraphJsonValueQuestTest(unittest.TestCase):

  def testMinimumArguments(self):
    quest = read_value.ReadGraphJsonValue.FromDict(_BASE_ARGUMENTS_GRAPH_JSON)
    expected = read_value.ReadGraphJsonValue(
        'base_perftests/perf_results.json', 'chart_name', 'trace_name')
    self.assertEqual(quest, expected)

  def testMissingChart(self):
    arguments = dict(_BASE_ARGUMENTS_GRAPH_JSON)
    del arguments['chart']
    quest = read_value.ReadGraphJsonValue.FromDict(arguments)
    expected = read_value.ReadGraphJsonValue(
        'base_perftests/perf_results.json', None, 'trace_name')
    self.assertEqual(quest, expected)

  def testMissingTrace(self):
    arguments = dict(_BASE_ARGUMENTS_GRAPH_JSON)
    del arguments['trace']
    quest = read_value.ReadGraphJsonValue.FromDict(arguments)
    expected = read_value.ReadGraphJsonValue(
        'base_perftests/perf_results.json', 'chart_name', None)
    self.assertEqual(quest, expected)


class _ReadValueExecutionTest(unittest.TestCase):

  def setUp(self):
    patcher = mock.patch('dashboard.services.isolate.Retrieve')
    self._retrieve = patcher.start()
    self.addCleanup(patcher.stop)

  def SetOutputFileContents(self, contents):
    self._retrieve.side_effect = (
        '{"files": {"chartjson-output.json": {"h": "output json hash"}}}',
        json.dumps(contents),
    )

  def assertReadValueError(self, execution, exception):
    self.assertTrue(execution.completed)
    self.assertTrue(execution.failed)
    self.assertIsInstance(execution.exception['traceback'], basestring)
    last_exception_line = execution.exception['traceback'].splitlines()[-1]
    self.assertTrue(
        last_exception_line.startswith(exception),
        'exception: %s' % (execution.exception,))

  def assertReadValueSuccess(self, execution):
    self.assertTrue(execution.completed)
    self.assertFalse(execution.failed)
    self.assertEqual(execution.result_arguments, {})

  def assertRetrievedOutputJson(self):
    expected_calls = [
        mock.call('server', 'output hash'),
        mock.call('server', 'output json hash'),
    ]
    self.assertEqual(self._retrieve.mock_calls, expected_calls)


class ReadHistogramsJsonValueTest(_ReadValueExecutionTest):

  def testReadHistogramsJsonValue(self):
    hist = histogram_module.Histogram('hist', 'count')
    hist.AddSample(0)
    hist.AddSample(1)
    hist.AddSample(2)
    histograms = histogram_set.HistogramSet([hist])
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORY_TAGS.name,
        generic_set.GenericSet(['group:tir_label']))
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORIES.name,
        generic_set.GenericSet(['story']))
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist.name, 'tir_label', 'story')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (0, 1, 2))
    self.assertRetrievedOutputJson()

  def testReadHistogramsJsonValueStoryNeedsEscape(self):
    hist = histogram_module.Histogram('hist', 'count')
    hist.AddSample(0)
    hist.AddSample(1)
    hist.AddSample(2)
    histograms = histogram_set.HistogramSet([hist])
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORY_TAGS.name,
        generic_set.GenericSet(['group:tir_label']))
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORIES.name,
        generic_set.GenericSet(['http://story']))
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist.name, 'tir_label', 'http://story')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (0, 1, 2))
    self.assertRetrievedOutputJson()

  def testReadHistogramsJsonValueStatistic(self):
    hist = histogram_module.Histogram('hist', 'count')
    hist.AddSample(0)
    hist.AddSample(1)
    hist.AddSample(2)
    histograms = histogram_set.HistogramSet([hist])
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORY_TAGS.name,
        generic_set.GenericSet(['group:tir_label']))
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORIES.name,
        generic_set.GenericSet(['story']))
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist.name,
        'tir_label', 'story', statistic='avg')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (1,))
    self.assertRetrievedOutputJson()

  def testReadHistogramsJsonValueStatisticNoSamples(self):
    hist = histogram_module.Histogram('hist', 'count')
    histograms = histogram_set.HistogramSet([hist])
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORY_TAGS.name,
        generic_set.GenericSet(['group:tir_label']))
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORIES.name,
        generic_set.GenericSet(['story']))
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist.name,
        'tir_label', 'story', statistic='avg')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueError(execution, 'ReadValueNoValues')

  def testReadHistogramsJsonValueMultipleHistograms(self):
    hist = histogram_module.Histogram('hist', 'count')
    hist.AddSample(0)
    hist.AddSample(1)
    hist.AddSample(2)
    hist2 = histogram_module.Histogram('hist', 'count')
    hist2.AddSample(0)
    hist2.AddSample(1)
    hist2.AddSample(2)
    hist3 = histogram_module.Histogram('some_other_histogram', 'count')
    hist3.AddSample(3)
    hist3.AddSample(4)
    hist3.AddSample(5)
    histograms = histogram_set.HistogramSet([hist, hist2, hist3])
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORY_TAGS.name,
        generic_set.GenericSet(['group:tir_label']))
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORIES.name,
        generic_set.GenericSet(['story']))
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist.name, 'tir_label', 'story')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (0, 1, 2, 0, 1, 2))
    self.assertRetrievedOutputJson()

  def testReadHistogramsTraceUrls(self):
    hist = histogram_module.Histogram('hist', 'count')
    hist.AddSample(0)
    hist.diagnostics[reserved_infos.TRACE_URLS.name] = (
        generic_set.GenericSet(['trace_url1', 'trace_url2']))
    hist2 = histogram_module.Histogram('hist2', 'count')
    hist2.diagnostics[reserved_infos.TRACE_URLS.name] = (
        generic_set.GenericSet(['trace_url3']))
    hist3 = histogram_module.Histogram('hist3', 'count')
    hist3.diagnostics[reserved_infos.TRACE_URLS.name] = (
        generic_set.GenericSet(['trace_url2']))
    histograms = histogram_set.HistogramSet([hist, hist2, hist3])
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name=hist.name)
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (0,))
    self.assertEqual(
        {
            'completed': True,
            'exception': None,
            'details': [
                {
                    'key': 'trace',
                    'value': 'trace_url1',
                    'url': 'trace_url1',
                },
                {
                    'key': 'trace',
                    'value': 'trace_url2',
                    'url': 'trace_url2',
                },
                {
                    'key': 'trace',
                    'value': 'trace_url3',
                    'url': 'trace_url3',
                },
            ],
        },
        execution.AsDict())
    self.assertRetrievedOutputJson()

  def testReadHistogramsDiagnosticRefSkipTraceUrls(self):
    hist = histogram_module.Histogram('hist', 'count')
    hist.AddSample(0)
    hist.diagnostics[reserved_infos.TRACE_URLS.name] = (
        generic_set.GenericSet(['trace_url1', 'trace_url2']))
    hist2 = histogram_module.Histogram('hist2', 'count')
    hist2.diagnostics[reserved_infos.TRACE_URLS.name] = (
        generic_set.GenericSet(['trace_url3']))
    hist2.diagnostics[reserved_infos.TRACE_URLS.name].guid = 'foo'
    histograms = histogram_set.HistogramSet([hist, hist2])
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name=hist.name)
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (0,))
    self.assertEqual(
        {
            'completed': True,
            'exception': None,
            'details': [
                {
                    'key': 'trace',
                    'value': 'trace_url1',
                    'url': 'trace_url1',
                },
                {
                    'key': 'trace',
                    'value': 'trace_url2',
                    'url': 'trace_url2',
                },
            ],
        },
        execution.AsDict())
    self.assertRetrievedOutputJson()

  def testReadHistogramsJsonValueWithNoTirLabel(self):
    hist = histogram_module.Histogram('hist', 'count')
    hist.AddSample(0)
    hist.AddSample(1)
    hist.AddSample(2)
    histograms = histogram_set.HistogramSet([hist])
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORY_TAGS.name,
        generic_set.GenericSet(['group:tir_label']))

    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name=hist.name, tir_label='tir_label')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (0, 1, 2))
    self.assertRetrievedOutputJson()

  def testReadHistogramsJsonValueWithNoStory(self):
    hist = histogram_module.Histogram('hist', 'count')
    hist.AddSample(0)
    hist.AddSample(1)
    hist.AddSample(2)
    histograms = histogram_set.HistogramSet([hist])
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORIES.name,
        generic_set.GenericSet(['story']))

    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name=hist.name, story='story')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (0, 1, 2))
    self.assertRetrievedOutputJson()

  def testReadHistogramsJsonValueSummaryTIRLabel(self):
    samples = []
    hists = []
    for i in range(10):
      hist = histogram_module.Histogram('hist', 'count')
      hist.AddSample(0)
      hist.AddSample(1)
      hist.AddSample(2)
      hist.diagnostics[reserved_infos.STORIES.name] = (
          generic_set.GenericSet(['story%d' % i]))
      hists.append(hist)
      samples.extend(hist.sample_values)

    histograms = histogram_set.HistogramSet(hists)
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORY_TAGS.name,
        generic_set.GenericSet(['group:tir_label']))

    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name=hists[0].name, tir_label='tir_label')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (sum(samples),))
    self.assertRetrievedOutputJson()

  def testReadHistogramsJsonValueSummary(self):
    samples = []
    hists = []
    for i in range(10):
      hist = histogram_module.Histogram('hist', 'count')
      hist.AddSample(0)
      hist.AddSample(1)
      hist.AddSample(2)
      hist.diagnostics[reserved_infos.STORIES.name] = (
          generic_set.GenericSet(['story%d' % i]))
      hist.diagnostics[reserved_infos.STORY_TAGS.name] = (
          generic_set.GenericSet(['group:tir_label1']))
      hists.append(hist)
      samples.extend(hist.sample_values)

    for i in range(10):
      hist = histogram_module.Histogram('hist', 'count')
      hist.AddSample(0)
      hist.AddSample(1)
      hist.AddSample(2)
      hist.diagnostics[reserved_infos.STORIES.name] = (
          generic_set.GenericSet(['another_story%d' % i]))
      hist.diagnostics[reserved_infos.STORY_TAGS.name] = (
          generic_set.GenericSet(['group:tir_label2']))
      hists.append(hist)
      samples.extend(hist.sample_values)

    histograms = histogram_set.HistogramSet(hists)
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORY_TAGS.name,
        generic_set.GenericSet(['group:tir_label']))

    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name=hists[0].name)
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (sum(samples),))
    self.assertRetrievedOutputJson()

  def testReadHistogramsJsonValueSummaryNoHistName(self):
    samples = []
    hists = []
    for i in range(10):
      hist = histogram_module.Histogram('hist', 'count')
      hist.AddSample(0)
      hist.AddSample(1)
      hist.AddSample(2)
      hist.diagnostics[reserved_infos.STORIES.name] = (
          generic_set.GenericSet(['story%d' % i]))
      hist.diagnostics[reserved_infos.STORY_TAGS.name] = (
          generic_set.GenericSet(['group:tir_label1']))
      hists.append(hist)
      samples.extend(hist.sample_values)

    histograms = histogram_set.HistogramSet(hists)
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORY_TAGS.name,
        generic_set.GenericSet(['group:tir_label']))

    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue('chartjson-output.json')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, ())
    self.assertRetrievedOutputJson()

  def testReadHistogramsJsonValueWithMissingFile(self):
    self._retrieve.return_value = '{"files": {}}'

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name='metric', tir_label='test')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueError(execution, 'ReadValueNoFile')

  def testReadHistogramsJsonValueEmptyHistogramSet(self):
    self.SetOutputFileContents([])

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name='metric', tir_label='test')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueError(execution, 'ReadValueNotFound')

  def testReadHistogramsJsonValueWithMissingHistogram(self):
    hist = histogram_module.Histogram('hist', 'count')
    histograms = histogram_set.HistogramSet([hist])
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name='does_not_exist')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueError(execution, 'ReadValueNotFound')

  def testReadHistogramsJsonValueWithNoValues(self):
    hist = histogram_module.Histogram('hist', 'count')
    histograms = histogram_set.HistogramSet([hist])
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name='chart')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueError(execution, 'ReadValueNotFound')

  def testReadHistogramsJsonValueTirLabelWithNoValues(self):
    hist = histogram_module.Histogram('hist', 'count')
    histograms = histogram_set.HistogramSet([hist])
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name='chart', tir_label='tir_label')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueError(execution, 'ReadValueNotFound')

  def testReadHistogramsJsonValueStoryWithNoValues(self):
    hist = histogram_module.Histogram('hist', 'count')
    histograms = histogram_set.HistogramSet([hist])
    self.SetOutputFileContents(histograms.AsDicts())

    quest = read_value.ReadHistogramsJsonValue(
        'chartjson-output.json', hist_name='chart', story='story')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueError(execution, 'ReadValueNotFound')


class ReadGraphJsonValueTest(_ReadValueExecutionTest):

  def testReadGraphJsonValue(self):
    self.SetOutputFileContents(
        {'chart': {'traces': {'trace': ['126444.869721', '0.0']}}})

    quest = read_value.ReadGraphJsonValue(
        'chartjson-output.json', 'chart', 'trace')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (126444.869721,))
    self.assertRetrievedOutputJson()

  def testReadGraphJsonValue_PerformanceBrowserTests(self):
    contents = {'chart': {'traces': {'trace': ['126444.869721', '0.0']}}}
    self._retrieve.side_effect = (
        '{"files": {"browser_tests/perf_results.json": {"h": "foo"}}}',
        json.dumps(contents),
    )

    quest = read_value.ReadGraphJsonValue(
        'performance_browser_tests/perf_results.json', 'chart', 'trace')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueSuccess(execution)
    self.assertEqual(execution.result_values, (126444.869721,))
    expected_calls = [
        mock.call('server', 'output hash'),
        mock.call('server', 'foo'),
    ]
    self.assertEqual(self._retrieve.mock_calls, expected_calls)

  def testReadGraphJsonValueWithMissingFile(self):
    self._retrieve.return_value = '{"files": {}}'

    quest = read_value.ReadGraphJsonValue(
        'base_perftests/perf_results.json', 'metric', 'test')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueError(execution, 'ReadValueNoFile')

  def testReadGraphJsonValueWithMissingChart(self):
    self.SetOutputFileContents({})

    quest = read_value.ReadGraphJsonValue(
        'chartjson-output.json', 'metric', 'test')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueError(execution, 'ReadValueChartNotFound')

  def testReadGraphJsonValueWithMissingTrace(self):
    self.SetOutputFileContents({'chart': {'traces': {}}})

    quest = read_value.ReadGraphJsonValue(
        'chartjson-output.json', 'chart', 'test')
    execution = quest.Start(None, 'server', 'output hash')
    execution.Poll()

    self.assertReadValueError(execution, 'ReadValueTraceNotFound')


@mock.patch('dashboard.services.isolate.Retrieve')
class EvaluatorTest(test.TestCase):

  def setUp(self):
    super(EvaluatorTest, self).setUp()
    self.maxDiff = None
    self.job = job_module.Job.New((), ())
    task_module.PopulateTaskGraph(
        self.job,
        read_value.CreateTasks(
            read_value.TaskOptions(
                test_options=run_test.TaskOptions(
                    build_options=find_isolate.TaskOptions(
                        builder='Some Builder',
                        target='telemetry_perf_tests',
                        bucket='luci.bucket',
                        change=change_module.Change.FromDict({
                            'commits': [{
                                'repository': 'chromium',
                                'git_hash': 'aaaaaaa',
                            }]
                        })),
                    swarming_server='some_server',
                    dimensions=[],
                    extra_args=[],
                    attempts=10),
                benchmark='some_benchmark',
                chart='some_chart',
                histogram_options=read_value.HistogramOptions(
                    tir_label='tir_label',
                    story='story',
                    statistic=None,
                ),
                graph_json_options=read_value.GraphJsonOptions(
                    trace='some_trace',),
                mode='histogram_sets',
            )))

  def testEvaluateSuccess_WithData(self, isolate_retrieve):
    # Seed the response to the call to the isolate service.
    histogram = histogram_module.Histogram('some_benchmark', 'count')
    histogram.AddSample(0)
    histogram.AddSample(1)
    histogram.AddSample(2)
    histograms = histogram_set.HistogramSet([histogram])
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORY_TAGS.name,
        generic_set.GenericSet(['group:tir_label']))
    histograms.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORIES.name, generic_set.GenericSet(['story']))
    isolate_retrieve.side_effect = itertools.chain(
        *itertools.repeat([('{"files": {"some_benchmark/perf_results.json": '
                            '{"h": "394890891823812873798734a"}}}'),
                           json.dumps(histograms.AsDicts())], 10))

    evaluator = evaluators.SequenceEvaluator(
        evaluators=(
            evaluators.FilteringEvaluator(
                predicate=evaluators.TaskTypeEq('find_isolate'),
                delegate=evaluators.SequenceEvaluator(
                    evaluators=(functools.partial(FakeFoundIsolate, self.job),
                                evaluators.TaskPayloadLiftingEvaluator()))),
            evaluators.FilteringEvaluator(
                predicate=evaluators.TaskTypeEq('run_test'),
                delegate=evaluators.SequenceEvaluator(
                    evaluators=(
                        functools.partial(FakeSuccessfulRunTest, self.job),
                        evaluators.TaskPayloadLiftingEvaluator()))),
            read_value.Evaluator(self.job),
        ))
    self.assertNotEqual({},
                        task_module.Evaluate(
                            self.job,
                            event_module.Event(
                                type='initiate', target_task=None, payload={}),
                            evaluator))

    # Ensure we find the find a value, and the histogram (?) associated with the
    # data we're looking for.
    task_module.Evaluate(
        self.job,
        event_module.Event(type='select', target_task=None, payload={}),
        evaluators.Selector(task_type='read_value'))

    self.assertEqual(
        {
            'read_value_chromium@aaaaaaa_%s' % (attempt,): {
                'benchmark': 'some_benchmark',
                'chart': 'some_chart',
                'mode': 'histogram_sets',
                'results_filename': 'some_benchmark/perf_results.json',
                'histogram_options': {
                    'tir_label': 'tir_label',
                    'story': 'story',
                    'statistic': None,
                },
                'graph_json_options': {
                    'trace': 'some_trace'
                },
                'status': 'completed',
                'result_values': [0, 1, 2],
                'tries': 1,
            } for attempt in range(10)
        },
        task_module.Evaluate(
            self.job,
            event_module.Event(type='select', target_task=None, payload={}),
            evaluators.Selector(task_type='read_value')))


  def testEvaluateFail_FileNotFound(self, *_):
    self.fail('Implement this!')

  def testEvaluateSuccess_HistogramSummary(self, *_):
    self.fail('Implement this!')

  def testEvaluateSuccess_HistogramSpecific(self, *_):
    self.fail('Implement this!')

  def testEvaluateFail_HistogramUnkonwnStat(self, *_):
    self.fail('Implement this!')

  def testEvaluateFail_GraphJsonChartNotFound(self, *_):
    self.fail('Implement this!')

  def testEvaluateFail_GraphJsonTraceNotFound(self, *_):
    self.fail('Implement this!')

def FakeFoundIsolate(job, task, *_):
  if task.status == 'completed':
    return None

  task.payload.update({
      'isolate_server': 'https://isolate.server',
      'isolate_hash': '12049adfa129339482234098',
  })
  return [
      lambda _: task_module.UpdateTask(
          job, task.id, new_state='completed', payload=task.payload)
  ]

def FakeSuccessfulRunTest(job, task, *_):
  if task.status == 'completed':
    return None

  task.payload.update({
      'isolate_server': 'https://isolate.server',
      'isolate_hash': '12334981aad2304ff1243458',
  })
  return [
      lambda _: task_module.UpdateTask(
          job, task.id, new_state='completed', payload=task.payload)
  ]
