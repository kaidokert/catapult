# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest
import mock

from py_utils import tempfile_ext

from telemetry import benchmark
from telemetry import story
from telemetry.internal.results import artifact_results
from telemetry.internal.results import base_test_results_unittest
from telemetry.internal.results import chart_json_output_formatter
from telemetry.internal.results import html_output_formatter
from telemetry.internal.results import page_test_results
from telemetry import page as page_module
from telemetry.testing import stream
from telemetry.value import failure
from telemetry.value import histogram
from telemetry.value import improvement_direction
from telemetry.value import scalar
from telemetry.value import skip
from telemetry.value import trace
from tracing.trace_data import trace_data
from tracing.value import histogram as histogram_module
from tracing.value import histogram_set
from tracing.value.diagnostics import diagnostic
from tracing.value.diagnostics import generic_set
from tracing.value.diagnostics import reserved_infos


class PageTestResultsTest(base_test_results_unittest.BaseTestResultsUnittest):
  def setUp(self):
    story_set = story.StorySet(base_dir=os.path.dirname(__file__))
    story_set.AddStory(page_module.Page("http://www.bar.com/", story_set,
                                        story_set.base_dir,
                                        name='http://www.bar.com/'))
    story_set.AddStory(page_module.Page("http://www.baz.com/", story_set,
                                        story_set.base_dir,
                                        name='http://www.baz.com/'))
    story_set.AddStory(page_module.Page("http://www.foo.com/", story_set,
                                        story_set.base_dir,
                                        name='http://www.foo.com/'))
    self.story_set = story_set

  @property
  def pages(self):
    return self.story_set.stories

  def testFailures(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(
        failure.FailureValue(self.pages[0], self.CreateException()))
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.DidRunPage(self.pages[1])

    self.assertEqual(set([self.pages[0]]), results.pages_that_failed)
    self.assertEqual(set([self.pages[1]]), results.pages_that_succeeded)

    self.assertEqual(2, len(results.all_page_runs))
    self.assertTrue(results.all_page_runs[0].failed)
    self.assertTrue(results.all_page_runs[1].ok)

  def testSkips(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(skip.SkipValue(self.pages[0], 'testing reason'))
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.DidRunPage(self.pages[1])

    self.assertTrue(results.all_page_runs[0].skipped)
    self.assertEqual(self.pages[0], results.all_page_runs[0].story)
    self.assertEqual(set([self.pages[0], self.pages[1]]),
                     results.pages_that_succeeded)

    self.assertEqual(2, len(results.all_page_runs))
    self.assertTrue(results.all_page_runs[0].skipped)
    self.assertTrue(results.all_page_runs[1].ok)

  def testPassesNoSkips(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(
        failure.FailureValue(self.pages[0], self.CreateException()))
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.DidRunPage(self.pages[1])

    results.WillRunPage(self.pages[2])
    results.AddValue(skip.SkipValue(self.pages[2], 'testing reason'))
    results.DidRunPage(self.pages[2])

    self.assertEqual(set([self.pages[0]]), results.pages_that_failed)
    self.assertEqual(set([self.pages[1], self.pages[2]]),
                     results.pages_that_succeeded)
    self.assertEqual(set([self.pages[1]]),
                     results.pages_that_succeeded_and_not_skipped)

    self.assertEqual(3, len(results.all_page_runs))
    self.assertTrue(results.all_page_runs[0].failed)
    self.assertTrue(results.all_page_runs[1].ok)
    self.assertTrue(results.all_page_runs[2].skipped)

  def testBasic(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.AddValue(scalar.ScalarValue(
        self.pages[1], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[1])

    results.PrintSummary()

    values = results.FindPageSpecificValuesForPage(self.pages[0], 'a')
    self.assertEquals(1, len(values))
    v = values[0]
    self.assertEquals(v.name, 'a')
    self.assertEquals(v.page, self.pages[0])

    values = results.FindAllPageSpecificValuesNamed('a')
    assert len(values) == 2

  def testAddValueWithStoryGroupingKeys(self):
    results = page_test_results.PageTestResults()
    self.pages[0].grouping_keys['foo'] = 'bar'
    self.pages[0].grouping_keys['answer'] = '42'
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[0])

    results.PrintSummary()

    values = results.FindPageSpecificValuesForPage(self.pages[0], 'a')
    v = values[0]
    self.assertEquals(v.grouping_keys['foo'], 'bar')
    self.assertEquals(v.grouping_keys['answer'], '42')
    self.assertEquals(v.tir_label, '42_bar')

  def testAddValueWithStoryGroupingKeysAndMatchingTirLabel(self):
    results = page_test_results.PageTestResults()
    self.pages[0].grouping_keys['foo'] = 'bar'
    self.pages[0].grouping_keys['answer'] = '42'
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP,
        tir_label='42_bar'))
    results.DidRunPage(self.pages[0])

    results.PrintSummary()

    values = results.FindPageSpecificValuesForPage(self.pages[0], 'a')
    v = values[0]
    self.assertEquals(v.grouping_keys['foo'], 'bar')
    self.assertEquals(v.grouping_keys['answer'], '42')
    self.assertEquals(v.tir_label, '42_bar')

  def testAddValueWithStoryGroupingKeysAndMismatchingTirLabel(self):
    results = page_test_results.PageTestResults()
    self.pages[0].grouping_keys['foo'] = 'bar'
    self.pages[0].grouping_keys['answer'] = '42'
    results.WillRunPage(self.pages[0])
    with self.assertRaises(AssertionError):
      results.AddValue(scalar.ScalarValue(
          self.pages[0], 'a', 'seconds', 3,
          improvement_direction=improvement_direction.UP,
          tir_label='another_label'))

  def testAddValueWithDuplicateStoryGroupingKeyFails(self):
    results = page_test_results.PageTestResults()
    self.pages[0].grouping_keys['foo'] = 'bar'
    results.WillRunPage(self.pages[0])
    with self.assertRaises(AssertionError):
      results.AddValue(scalar.ScalarValue(
          self.pages[0], 'a', 'seconds', 3,
          improvement_direction=improvement_direction.UP,
          grouping_keys={'foo': 'bar'}))

  def testUrlIsInvalidValue(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    self.assertRaises(
        AssertionError,
        lambda: results.AddValue(scalar.ScalarValue(
            self.pages[0], 'url', 'string', 'foo',
            improvement_direction=improvement_direction.UP)))

  def testAddSummaryValueWithPageSpecified(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    self.assertRaises(
        AssertionError,
        lambda: results.AddSummaryValue(scalar.ScalarValue(
            self.pages[0], 'a', 'units', 3,
            improvement_direction=improvement_direction.UP)))

  def testUnitChange(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    self.assertRaises(
        AssertionError,
        lambda: results.AddValue(scalar.ScalarValue(
            self.pages[1], 'a', 'foobgrobbers', 3,
            improvement_direction=improvement_direction.UP)))

  def testTypeChange(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    self.assertRaises(
        AssertionError,
        lambda: results.AddValue(histogram.HistogramValue(
            self.pages[1], 'a', 'seconds',
            raw_value_json='{"buckets": [{"low": 1, "high": 2, "count": 1}]}',
            improvement_direction=improvement_direction.UP)))

  def testGetPagesThatSucceededAllPagesFail(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.AddValue(failure.FailureValue.FromMessage(self.pages[0], 'message'))
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.AddValue(scalar.ScalarValue(
        self.pages[1], 'a', 'seconds', 7,
        improvement_direction=improvement_direction.UP))
    results.AddValue(failure.FailureValue.FromMessage(self.pages[1], 'message'))
    results.DidRunPage(self.pages[1])

    results.PrintSummary()
    self.assertEquals(0, len(results.pages_that_succeeded))

  def testGetSuccessfulPageValuesMergedNoFailures(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    self.assertEquals(1, len(results.all_page_specific_values))
    results.DidRunPage(self.pages[0])

  def testGetAllValuesForSuccessfulPages(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    value1 = scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP)
    results.AddValue(value1)
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    value2 = scalar.ScalarValue(
        self.pages[1], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP)
    results.AddValue(value2)
    results.DidRunPage(self.pages[1])

    results.WillRunPage(self.pages[2])
    value3 = scalar.ScalarValue(
        self.pages[2], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP)
    results.AddValue(value3)
    results.DidRunPage(self.pages[2])

    self.assertEquals(
        [value1, value2, value3], results.all_page_specific_values)

  def testGetAllValuesForSuccessfulPagesOnePageFails(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    value1 = scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP)
    results.AddValue(value1)
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    value2 = failure.FailureValue.FromMessage(self.pages[1], 'Failure')
    results.AddValue(value2)
    results.DidRunPage(self.pages[1])

    results.WillRunPage(self.pages[2])
    value3 = scalar.ScalarValue(
        self.pages[2], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP)
    results.AddValue(value3)
    results.DidRunPage(self.pages[2])

    self.assertEquals(
        [value1, value2, value3], results.all_page_specific_values)

  def testFindValues(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    v0 = scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP)
    results.AddValue(v0)
    v1 = scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 4,
        improvement_direction=improvement_direction.UP)
    results.AddValue(v1)
    results.DidRunPage(self.pages[1])

    values = results.FindValues(lambda v: v.value == 3)
    self.assertEquals([v0], values)

  def testValueWithTIRLabel(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    v0 = scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3, tir_label='foo',
        improvement_direction=improvement_direction.UP)
    results.AddValue(v0)
    v1 = scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3, tir_label='bar',
        improvement_direction=improvement_direction.UP)
    results.AddValue(v1)
    results.DidRunPage(self.pages[0])

    values = results.FindAllPageSpecificValuesFromIRNamed('foo', 'a')
    self.assertEquals([v0], values)

  def testTraceValue(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(trace.TraceValue(
        None, trace_data.CreateTraceDataFromRawData([[{'test': 1}]])))
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.AddValue(trace.TraceValue(
        None, trace_data.CreateTraceDataFromRawData([[{'test': 2}]])))
    results.DidRunPage(self.pages[1])

    results.PrintSummary()

    values = results.FindAllTraceValues()
    self.assertEquals(2, len(values))

  def testCleanUpCleansUpTraceValues(self):
    results = page_test_results.PageTestResults()
    v0 = trace.TraceValue(
        None, trace_data.CreateTraceDataFromRawData([{'test': 1}]))
    v1 = trace.TraceValue(
        None, trace_data.CreateTraceDataFromRawData([{'test': 2}]))

    results.WillRunPage(self.pages[0])
    results.AddValue(v0)
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.AddValue(v1)
    results.DidRunPage(self.pages[1])

    results.CleanUp()
    self.assertTrue(v0.cleaned_up)
    self.assertTrue(v1.cleaned_up)

  def testNoTracesLeftAfterCleanUp(self):
    results = page_test_results.PageTestResults()
    v0 = trace.TraceValue(None,
                          trace_data.CreateTraceDataFromRawData([{'test': 1}]))
    v1 = trace.TraceValue(None,
                          trace_data.CreateTraceDataFromRawData([{'test': 2}]))

    results.WillRunPage(self.pages[0])
    results.AddValue(v0)
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.AddValue(v1)
    results.DidRunPage(self.pages[1])

    results.CleanUp()
    self.assertFalse(results.FindAllTraceValues())

  def testPrintSummaryDisabledResults(self):
    output_stream = stream.TestOutputStream()
    output_formatters = []
    benchmark_metadata = benchmark.BenchmarkMetadata(
        'benchmark_name', 'benchmark_description')
    output_formatters.append(
        chart_json_output_formatter.ChartJsonOutputFormatter(
            output_stream, benchmark_metadata))
    output_formatters.append(html_output_formatter.HtmlOutputFormatter(
        output_stream, benchmark_metadata, True))
    results = page_test_results.PageTestResults(
        output_formatters=output_formatters, benchmark_enabled=False)
    results.PrintSummary()
    self.assertEquals(
        output_stream.output_data,
        '{\n  \"enabled\": false,\n  ' +
        '\"benchmark_name\": \"benchmark_name\"\n}\n')

  def testImportHistogramDicts(self):
    hs = histogram_set.HistogramSet()
    hs.AddHistogram(histogram_module.Histogram('foo', 'count'))
    hs.AddSharedDiagnostic('bar', generic_set.GenericSet(['baz']))
    histogram_dicts = hs.AsDicts()
    results = page_test_results.PageTestResults()
    results.telemetry_info.benchmark_start_epoch = 1501773200
    results.WillRunPage(self.pages[0])
    results.ImportHistogramDicts(histogram_dicts)
    results.DidRunPage(self.pages[0])
    self.assertEqual(results.AsHistogramDicts(), histogram_dicts)

  def testAddSharedDiagnostic(self):
    results = page_test_results.PageTestResults()
    results.telemetry_info.benchmark_start_epoch = 1501773200
    results.WillRunPage(self.pages[0])
    results.DidRunPage(self.pages[0])
    results.CleanUp()
    results.AddSharedDiagnostic(
        reserved_infos.BENCHMARKS.name,
        generic_set.GenericSet(['benchmark_name']))

    benchmark_metadata = benchmark.BenchmarkMetadata(
        'benchmark_name', 'benchmark_description')
    results.PopulateHistogramSet(benchmark_metadata)

    histogram_dicts = results.AsHistogramDicts()
    self.assertEquals(1, len(histogram_dicts))

    diag = diagnostic.Diagnostic.FromDict(histogram_dicts[0])
    self.assertIsInstance(diag, generic_set.GenericSet)

  def testPopulateHistogramSet_UsesScalarValueData(self):
    results = page_test_results.PageTestResults()
    results.telemetry_info.benchmark_start_epoch = 1501773200
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[0])
    results.CleanUp()

    benchmark_metadata = benchmark.BenchmarkMetadata(
        'benchmark_name', 'benchmark_description')
    results.PopulateHistogramSet(benchmark_metadata)

    self.assertEquals(1, len(results.histograms))
    self.assertEquals('a', list(results.histograms)[0].name)

  def testPopulateHistogramSet_UsesHistogramSetData(self):
    original_diagnostic = generic_set.GenericSet(['benchmark_name'])

    results = page_test_results.PageTestResults()
    results.telemetry_info.benchmark_start_epoch = 1501773200
    results.WillRunPage(self.pages[0])
    results.histograms.AddHistogram(histogram_module.Histogram('foo', 'count'))
    results.histograms.AddSharedDiagnostic(
        reserved_infos.BENCHMARKS.name, original_diagnostic)
    results.DidRunPage(self.pages[0])
    results.CleanUp()

    benchmark_metadata = benchmark.BenchmarkMetadata(
        'benchmark_name', 'benchmark_description')
    results.PopulateHistogramSet(benchmark_metadata)

    histogram_dicts = results.AsHistogramDicts()
    self.assertEquals(2, len(histogram_dicts))

    hs = histogram_set.HistogramSet()
    hs.ImportDicts(histogram_dicts)

    diag = hs.LookupDiagnostic(original_diagnostic.guid)
    self.assertIsInstance(diag, generic_set.GenericSet)


class PageTestResultsFilterTest(unittest.TestCase):
  def setUp(self):
    story_set = story.StorySet(base_dir=os.path.dirname(__file__))
    story_set.AddStory(
        page_module.Page('http://www.foo.com/', story_set, story_set.base_dir,
                         name='http://www.foo.com'))
    story_set.AddStory(
        page_module.Page('http://www.bar.com/', story_set, story_set.base_dir,
                         name='http://www.bar.com/'))
    self.story_set = story_set

  @property
  def pages(self):
    return self.story_set.stories

  def testFilterValue(self):
    def AcceptValueNamed_a(name, _):
      return name == 'a'
    results = page_test_results.PageTestResults(
        should_add_value=AcceptValueNamed_a)
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'b', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.AddValue(scalar.ScalarValue(
        self.pages[1], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.AddValue(scalar.ScalarValue(
        self.pages[1], 'd', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[1])
    results.PrintSummary()
    self.assertEquals(
        [('a', 'http://www.foo.com/'), ('a', 'http://www.bar.com/')],
        [(v.name, v.page.url) for v in results.all_page_specific_values])

  def testFilterValueWithImportHistogramDicts(self):
    def AcceptValueNamed_a(name, _):
      return name == 'a'
    hs = histogram_set.HistogramSet()
    hs.AddHistogram(histogram_module.Histogram('a', 'count'))
    hs.AddHistogram(histogram_module.Histogram('b', 'count'))
    results = page_test_results.PageTestResults(
        should_add_value=AcceptValueNamed_a)
    results.WillRunPage(self.pages[0])
    results.ImportHistogramDicts(hs.AsDicts())
    results.DidRunPage(self.pages[0])

    new_hs = histogram_set.HistogramSet()
    new_hs.ImportDicts(results.AsHistogramDicts())
    self.assertEquals(len(new_hs), 1)

  def testFilterIsFirstResult(self):
    def AcceptSecondValues(_, is_first_result):
      return not is_first_result
    results = page_test_results.PageTestResults(
        should_add_value=AcceptSecondValues)

    # First results (filtered out)
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 7,
        improvement_direction=improvement_direction.UP))
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'b', 'seconds', 8,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[0])
    results.WillRunPage(self.pages[1])
    results.AddValue(scalar.ScalarValue(
        self.pages[1], 'a', 'seconds', 5,
        improvement_direction=improvement_direction.UP))
    results.AddValue(scalar.ScalarValue(
        self.pages[1], 'd', 'seconds', 6,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[1])

    # Second results
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'b', 'seconds', 4,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[0])
    results.WillRunPage(self.pages[1])
    results.AddValue(scalar.ScalarValue(
        self.pages[1], 'a', 'seconds', 1,
        improvement_direction=improvement_direction.UP))
    results.AddValue(scalar.ScalarValue(
        self.pages[1], 'd', 'seconds', 2,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[1])
    results.PrintSummary()
    expected_values = [
        ('a', 'http://www.foo.com/', 3),
        ('b', 'http://www.foo.com/', 4),
        ('a', 'http://www.bar.com/', 1),
        ('d', 'http://www.bar.com/', 2)]
    actual_values = [(v.name, v.page.url, v.value)
                     for v in results.all_page_specific_values]
    self.assertEquals(expected_values, actual_values)

  def testFailureValueCannotBeFiltered(self):
    def AcceptValueNamed_a(name, _):
      return name == 'a'
    results = page_test_results.PageTestResults(
        should_add_value=AcceptValueNamed_a)
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'b', 'seconds', 8,
        improvement_direction=improvement_direction.UP))
    failure_value = failure.FailureValue.FromMessage(self.pages[0], 'failure')
    results.AddValue(failure_value)
    results.DidRunPage(self.pages[0])
    results.PrintSummary()

    # Although predicate says only accept values named 'a', the failure value is
    # added anyway.
    self.assertEquals(len(results.all_page_specific_values), 1)
    self.assertIn(failure_value, results.all_page_specific_values)

  def testSkipValueCannotBeFiltered(self):
    def AcceptValueNamed_a(name, _):
      return name == 'a'
    results = page_test_results.PageTestResults(
        should_add_value=AcceptValueNamed_a)
    results.WillRunPage(self.pages[0])
    skip_value = skip.SkipValue(self.pages[0], 'skip for testing')
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'b', 'seconds', 8,
        improvement_direction=improvement_direction.UP))
    results.AddValue(skip_value)
    results.DidRunPage(self.pages[0])
    results.PrintSummary()

    # Although predicate says only accept value with named 'a', skip value is
    # added anyway.
    self.assertEquals(len(results.all_page_specific_values), 1)
    self.assertIn(skip_value, results.all_page_specific_values)

  def testFilterHistogram(self):
    def AcceptValueNamed_a(name, _):
      return name == 'a'
    results = page_test_results.PageTestResults(
        should_add_value=AcceptValueNamed_a)
    results.WillRunPage(self.pages[0])
    results.AddHistogram(histogram_module.Histogram('a', 'count'))
    results.AddHistogram(histogram_module.Histogram('b', 'count'))

    self.assertEquals(len(results.histograms), 1)
    self.assertEquals(results.histograms.GetFirstHistogram().name, 'a')

  @mock.patch('py_utils.cloud_storage.Insert')
  def testUploadArtifactsToCloud(self, cloud_storage_insert_patch):
    with tempfile_ext.NamedTemporaryDirectory(
        prefix='artifact_tests') as tempdir:

      ar = artifact_results.ArtifactResults(tempdir)
      results = page_test_results.PageTestResults(
          upload_bucket='abc', artifact_results=ar)


      with results.CreateArtifact('story1', 'screenshot') as screenshot1:
        pass

      with results.CreateArtifact('story2', 'log') as log2:
        pass

      results.UploadArtifactsToCloud()
      cloud_storage_insert_patch.assert_has_calls(
          [mock.call('abc', mock.ANY, screenshot1.name),
           mock.call('abc', mock.ANY, log2.name)],
          any_order=True)

  @mock.patch('py_utils.cloud_storage.Insert')
  def testUploadArtifactsToCloud_withNoOpArtifact(
      self, cloud_storage_insert_patch):
    del cloud_storage_insert_patch  # unused
    with tempfile_ext.NamedTemporaryDirectory(
        prefix='artifact_tests') as tempdir:

      ar = artifact_results.NoopArtifactResults(tempdir)
      results = page_test_results.PageTestResults(
          upload_bucket='abc', artifact_results=ar)


      with results.CreateArtifact('story1', 'screenshot'):
        pass

      with results.CreateArtifact('story2', 'log'):
        pass

      # Just make sure that this does not crash
      results.UploadArtifactsToCloud()
