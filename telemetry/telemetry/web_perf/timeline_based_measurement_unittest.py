# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import shutil
import tempfile
import unittest

from telemetry import benchmark
from telemetry.core import util
from telemetry import decorators
from telemetry.internal.results import page_test_results
from telemetry.internal import story_runner
from telemetry import page
from telemetry import story
from telemetry.testing import options_for_unittests
from telemetry.web_perf import timeline_based_measurement


class TestPage(page.Page):
  def __init__(self, story_set, run_side_effect):
    """A simple customizable test page.

    Args:
      run_side_effect: Side effect of the story's RunPageInteractions method.
        It should be a callable taking an action_runner.
    """
    super(TestPage, self).__init__(
        'file://interaction_enabled_page.html', story_set,
        name='interaction_enabled_page', base_dir=story_set.base_dir)
    self._run_side_effect = run_side_effect

  def RunPageInteractions(self, action_runner):
    if self._run_side_effect is not None:
      self._run_side_effect(action_runner)


class TestTimelineBenchmark(benchmark.Benchmark):
  def __init__(self, story_run_side_effect=None):
    super(TestTimelineBenchmark, self).__init__()
    self._story_run_side_effect = story_run_side_effect

  def CreateStorySet(self, _):
    story_set = story.StorySet(base_dir=util.GetUnittestDataDir())
    story_set.AddStory(TestPage(story_set, self._story_run_side_effect))
    return story_set

  def CreateCoreTimelineBasedMeasurementOptions(self):
    options = timeline_based_measurement.Options()
    options.config.enable_chrome_trace = True
    options.SetTimelineBasedMetrics(['sampleMetric'])
    return options

  @classmethod
  def Name(cls):
    return 'test_timeline_benchmark'


class TimelineBasedMeasurementTest(unittest.TestCase):
  """Tests for TimelineBasedMeasurement which allows to record traces."""

  def setUp(self):
    self.options = options_for_unittests.GetRunOptions(
        output_dir=tempfile.mkdtemp())
    self.options.intermediate_dir = os.path.join(
        self.options.output_dir, 'artifacts')

  def tearDown(self):
    shutil.rmtree(self.options.output_dir)

  def RunBenchmarkAndReadResults(self, test_benchmark):
    story_runner.RunBenchmark(test_benchmark, self.options)
    test_results = page_test_results.ReadIntermediateResults(
        self.options.intermediate_dir)['testResults']
    self.assertEqual(len(test_results), 1)
    return test_results[0]

  @decorators.Isolated
  def testTraceCaptureUponSuccess(self):
    test_benchmark = TestTimelineBenchmark()
    results = self.RunBenchmarkAndReadResults(test_benchmark)
    self.assertEqual(results['status'], 'PASS')
    # Assert that we can find a Chrome trace.
    self.assertTrue(any(
        n.startswith('trace/traceEvents') for n in results['artifacts']))

  @decorators.Isolated
  def testTraceCaptureUponFailure(self):
    test_benchmark = TestTimelineBenchmark(
        story_run_side_effect=lambda a: a.TapElement('#does-not-exist'))
    results = self.RunBenchmarkAndReadResults(test_benchmark)
    self.assertEqual(results['status'], 'FAIL')
    # Assert that we can find a Chrome trace.
    self.assertTrue(any(
        n.startswith('trace/traceEvents') for n in results['artifacts']))
