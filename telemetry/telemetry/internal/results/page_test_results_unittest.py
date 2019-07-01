# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import StringIO
import unittest

from py_utils import tempfile_ext
import mock

from telemetry import story
from telemetry.internal.results import base_test_results_unittest
from telemetry.internal.results import chart_json_output_formatter
from telemetry.internal.results import html_output_formatter
from telemetry.internal.results import page_test_results
from telemetry.internal.results import results_processor
from telemetry import page as page_module
from telemetry.value import improvement_direction
from telemetry.value import scalar
from tracing.trace_data import trace_data
from tracing.value import histogram as histogram_module
from tracing.value import histogram_set
from tracing.value.diagnostics import diagnostic
from tracing.value.diagnostics import generic_set
from tracing.value.diagnostics import reserved_infos


class TelemetryInfoTest(unittest.TestCase):
  def testTraceLocalPathWithoutLabel(self):
    ti = page_test_results.TelemetryInfo(
        benchmark_name='benchmark',
        benchmark_description='foo',
        output_dir='/tmp')
    story_set = story.StorySet()
    bar_story = page_module.Page("http://www.bar.com/", story_set,
                                 name='http://www.bar.com/')
    story_set.AddStory(bar_story)
    ti.WillRunStory(bar_story, None)
    self.assertIn('www_bar_com', ti.trace_local_path)
    self.assertNotIn('custom_label', ti.trace_local_path)

  def testTraceLocalPathWithLabel(self):
    ti = page_test_results.TelemetryInfo(
        benchmark_name='benchmark',
        benchmark_description='foo',
        results_label='custom_label',
        output_dir='/tmp')
    story_set = story.StorySet()
    bar_story = page_module.Page("http://www.bar.com/", story_set,
                                 name='http://www.bar.com/')
    story_set.AddStory(bar_story)
    ti.WillRunStory(bar_story, None)
    self.assertIn('www_bar_com', ti.trace_local_path)
    self.assertIn('custom_label', ti.trace_local_path)


class PageTestResultsTest(base_test_results_unittest.BaseTestResultsUnittest):
  def setUp(self):
    story_set = story.StorySet()
    story_set.AddStory(page_module.Page("http://www.bar.com/", story_set,
                                        name='http://www.bar.com/'))
    story_set.AddStory(page_module.Page("http://www.baz.com/", story_set,
                                        name='http://www.baz.com/'))
    story_set.AddStory(page_module.Page("http://www.foo.com/", story_set,
                                        name='http://www.foo.com/'))
    self.story_set = story_set

  @property
  def pages(self):
    return self.story_set.stories

  def testFailures(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.Fail(self.CreateException())
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.DidRunPage(self.pages[1])

    self.assertEqual(set([self.pages[0]]), results.pages_that_failed)
    self.assertEqual(set([self.pages[1]]), results.pages_that_succeeded)

    self.assertEqual(len(results.all_page_runs), 2)
    self.assertTrue(results.had_failures)
    self.assertTrue(results.all_page_runs[0].failed)
    self.assertTrue(results.all_page_runs[1].ok)

  def testSkips(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.Skip('testing reason')
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

  def testInterruptMiddleRun(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[1])
    results.DidRunPage(self.pages[1])
    results.InterruptBenchmark(self.pages, 2)

    self.assertEqual(6, len(results.all_page_runs))
    self.assertTrue(results.all_page_runs[0].ok)
    self.assertTrue(results.all_page_runs[1].skipped)
    self.assertTrue(results.all_page_runs[2].skipped)
    self.assertTrue(results.all_page_runs[3].skipped)
    self.assertTrue(results.all_page_runs[4].skipped)
    self.assertTrue(results.all_page_runs[5].skipped)

  def testInterruptBeginningRun(self):
    results = page_test_results.PageTestResults()
    results.InterruptBenchmark(self.pages, 1)

    self.assertTrue(results.all_page_runs[0].skipped)
    self.assertEqual(self.pages[0], results.all_page_runs[0].story)
    self.assertEqual(set([]),
                     results.pages_that_succeeded_and_not_skipped)

    self.assertEqual(3, len(results.all_page_runs))
    self.assertTrue(results.all_page_runs[0].skipped)
    self.assertTrue(results.all_page_runs[1].skipped)
    self.assertTrue(results.all_page_runs[2].skipped)

  def testPassesNoSkips(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.Fail(self.CreateException())
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.DidRunPage(self.pages[1])

    results.WillRunPage(self.pages[2])
    results.Skip('testing reason')
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
    self.assertEquals(v.grouping_label, '42_bar')

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

  def testGetPagesThatSucceededAllPagesFail(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.Fail('message')
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    results.AddValue(scalar.ScalarValue(
        self.pages[1], 'a', 'seconds', 7,
        improvement_direction=improvement_direction.UP))
    results.Fail('message')
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

  def testAddTraces(self):
    with tempfile_ext.NamedTemporaryDirectory() as tempdir:
      results = page_test_results.PageTestResults(output_dir=tempdir)
      results.WillRunPage(self.pages[0])
      results.AddTraces(trace_data.CreateTestTrace(1))
      results.DidRunPage(self.pages[0])

      results.WillRunPage(self.pages[1])
      results.AddTraces(trace_data.CreateTestTrace(2))
      results.DidRunPage(self.pages[1])

      runs = list(results.IterRunsWithTraces())
      self.assertEquals(2, len(runs))

  def testPrintSummaryDisabledResults(self):
    output_stream = StringIO.StringIO()
    output_formatters = []
    output_formatters.append(
        chart_json_output_formatter.ChartJsonOutputFormatter(output_stream))
    output_formatters.append(html_output_formatter.HtmlOutputFormatter(
        output_stream, reset_results=True))
    results = page_test_results.PageTestResults(
        output_formatters=output_formatters,
        benchmark_name='benchmark_name',
        benchmark_description='benchmark_description',
        benchmark_enabled=False)
    results.PrintSummary()
    self.assertEquals(
        output_stream.getvalue(),
        '{\n  \"enabled\": false,\n  ' +
        '\"benchmark_name\": \"benchmark_name\"\n}\n')

  def testImportHistogramDicts(self):
    hs = histogram_set.HistogramSet()
    hs.AddHistogram(histogram_module.Histogram('foo', 'count'))
    hs.AddSharedDiagnosticToAllHistograms(
        'bar', generic_set.GenericSet(['baz']))
    histogram_dicts = hs.AsDicts()
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.ImportHistogramDicts(histogram_dicts)
    results.DidRunPage(self.pages[0])
    self.assertEqual(results.AsHistogramDicts(), histogram_dicts)

  def testImportHistogramDicts_DelayedImport(self):
    hs = histogram_set.HistogramSet()
    hs.AddHistogram(histogram_module.Histogram('foo', 'count'))
    hs.AddSharedDiagnosticToAllHistograms(
        'bar', generic_set.GenericSet(['baz']))
    histogram_dicts = hs.AsDicts()
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.ImportHistogramDicts(histogram_dicts, import_immediately=False)
    results.DidRunPage(self.pages[0])
    self.assertEqual(len(results.AsHistogramDicts()), 0)
    results.PopulateHistogramSet()
    self.assertEqual(results.AsHistogramDicts(), histogram_dicts)

  def testAddSharedDiagnosticToAllHistograms(self):
    results = page_test_results.PageTestResults(
        benchmark_name='benchmark_name')
    results.WillRunPage(self.pages[0])
    results.DidRunPage(self.pages[0])
    results.AddSharedDiagnosticToAllHistograms(
        reserved_infos.BENCHMARKS.name,
        generic_set.GenericSet(['benchmark_name']))

    results.PopulateHistogramSet()

    histogram_dicts = results.AsHistogramDicts()
    self.assertEquals(1, len(histogram_dicts))

    diag = diagnostic.Diagnostic.FromDict(histogram_dicts[0])
    self.assertIsInstance(diag, generic_set.GenericSet)

  def testPopulateHistogramSet_UsesScalarValueData(self):
    results = page_test_results.PageTestResults()
    results.WillRunPage(self.pages[0])
    results.AddValue(scalar.ScalarValue(
        self.pages[0], 'a', 'seconds', 3,
        improvement_direction=improvement_direction.UP))
    results.DidRunPage(self.pages[0])

    results.PopulateHistogramSet()

    hs = histogram_set.HistogramSet()
    hs.ImportDicts(results.AsHistogramDicts())
    self.assertEquals(1, len(hs))
    self.assertEquals('a', hs.GetFirstHistogram().name)

  def testPopulateHistogramSet_UsesHistogramSetData(self):
    results = page_test_results.PageTestResults(
        benchmark_name='benchmark_name')
    results.WillRunPage(self.pages[0])
    results.AddHistogram(histogram_module.Histogram('foo', 'count'))
    results.DidRunPage(self.pages[0])
    results.PopulateHistogramSet()

    histogram_dicts = results.AsHistogramDicts()
    self.assertEquals(7, len(histogram_dicts))

    hs = histogram_set.HistogramSet()
    hs.ImportDicts(histogram_dicts)

    hist = hs.GetHistogramNamed('foo')
    self.assertItemsEqual(hist.diagnostics[reserved_infos.BENCHMARKS.name],
                          ['benchmark_name'])


class PageTestResultsFilterTest(unittest.TestCase):
  def setUp(self):
    story_set = story.StorySet()
    story_set.AddStory(
        page_module.Page('http://www.foo.com/', story_set,
                         name='http://www.foo.com'))
    story_set.AddStory(
        page_module.Page('http://www.bar.com/', story_set,
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
    def AcceptValueStartsWith_a(name, _):
      return name.startswith('a')
    hs = histogram_set.HistogramSet()
    hs.AddHistogram(histogram_module.Histogram('a', 'count'))
    hs.AddHistogram(histogram_module.Histogram('b', 'count'))
    results = page_test_results.PageTestResults(
        should_add_value=AcceptValueStartsWith_a)
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

  def testFilterHistogram(self):
    def AcceptValueNamed_a(name, _):
      return name.startswith('a')
    results = page_test_results.PageTestResults(
        should_add_value=AcceptValueNamed_a)
    results.WillRunPage(self.pages[0])
    hist0 = histogram_module.Histogram('a', 'count')
    # Necessary to make sure avg is added
    hist0.AddSample(0)
    results.AddHistogram(hist0)
    hist1 = histogram_module.Histogram('b', 'count')
    hist1.AddSample(0)
    results.AddHistogram(hist1)

    # Filter out the diagnostics
    dicts = results.AsHistogramDicts()
    histogram_dicts = []
    for d in dicts:
      if 'name' in d:
        histogram_dicts.append(d)

    self.assertEquals(len(histogram_dicts), 1)
    self.assertEquals(histogram_dicts[0]['name'], 'a')

  def testFilterHistogram_AllStatsNotFiltered(self):
    def AcceptNonAverage(name, _):
      return not name.endswith('avg')
    results = page_test_results.PageTestResults(
        should_add_value=AcceptNonAverage)
    results.WillRunPage(self.pages[0])
    hist0 = histogram_module.Histogram('a', 'count')
    # Necessary to make sure avg is added
    hist0.AddSample(0)
    results.AddHistogram(hist0)
    hist1 = histogram_module.Histogram('a_avg', 'count')
    # Necessary to make sure avg is added
    hist1.AddSample(0)
    results.AddHistogram(hist1)

    # Filter out the diagnostics
    dicts = results.AsHistogramDicts()
    histogram_dicts = []
    for d in dicts:
      if 'name' in d:
        histogram_dicts.append(d)

    self.assertEquals(len(histogram_dicts), 2)
    histogram_dicts.sort(key=lambda h: h['name'])

    self.assertEquals(len(histogram_dicts), 2)
    self.assertEquals(histogram_dicts[0]['name'], 'a')
    self.assertEquals(histogram_dicts[1]['name'], 'a_avg')

  @mock.patch('py_utils.cloud_storage.Insert')
  def testUploadArtifactsToCloud(self, cloud_storage_insert_patch):
    cs_path_name = 'https://cs_foo'
    cloud_storage_insert_patch.return_value = cs_path_name
    with tempfile_ext.NamedTemporaryDirectory(
        prefix='artifact_tests') as tempdir:

      results = page_test_results.PageTestResults(
          upload_bucket='abc', output_dir=tempdir)

      results.WillRunPage(self.pages[0])
      with results.CreateArtifact('screenshot') as screenshot1:
        pass
      results.DidRunPage(self.pages[0])

      results.WillRunPage(self.pages[1])
      with results.CreateArtifact('log') as log2:
        pass
      results.DidRunPage(self.pages[1])

      results_processor.UploadArtifactsToCloud(results)
      cloud_storage_insert_patch.assert_has_calls(
          [mock.call('abc', mock.ANY, screenshot1.name),
           mock.call('abc', mock.ANY, log2.name)],
          any_order=True)

      # Assert that the path is now the cloud storage path
      for run in results._all_page_runs:
        for artifact in run.IterArtifacts():
          self.assertEquals(cs_path_name, artifact.url)

  @mock.patch('py_utils.cloud_storage.Insert')
  def testUploadArtifactsToCloud_withNoOpArtifact(
      self, cloud_storage_insert_patch):
    del cloud_storage_insert_patch  # unused

    results = page_test_results.PageTestResults(
        upload_bucket='abc', output_dir=None)


    results.WillRunPage(self.pages[0])
    with results.CreateArtifact('screenshot'):
      pass
    results.DidRunPage(self.pages[0])

    results.WillRunPage(self.pages[1])
    with results.CreateArtifact('log'):
      pass
    results.DidRunPage(self.pages[1])

    # Just make sure that this does not crash
    results_processor.UploadArtifactsToCloud(results)

  def testCreateArtifactsForDifferentPages(self):
    with tempfile_ext.NamedTemporaryDirectory() as tempdir:
      results = page_test_results.PageTestResults(output_dir=tempdir)

      results.WillRunPage(self.pages[0])
      with results.CreateArtifact('log') as log_file:
        log_file.write('page0\n')
      results.DidRunPage(self.pages[0])

      results.WillRunPage(self.pages[1])
      with results.CreateArtifact('log') as log_file:
        log_file.write('page1\n')
      results.DidRunPage(self.pages[1])

      log0_path = results._all_page_runs[0].GetArtifact('log').local_path
      with open(log0_path) as f:
        self.assertEqual(f.read(), 'page0\n')

      log1_path = results._all_page_runs[1].GetArtifact('log').local_path
      with open(log1_path) as f:
        self.assertEqual(f.read(), 'page1\n')
