# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys
import unittest

from telemetry import benchmark
from telemetry import benchmark_list
from telemetry import story as story_module
from telemetry import page as page_module
import mock


class BenchmarkFoo(benchmark.Benchmark):
  """Benchmark foo for testing."""

  def page_set(self):
    page = page_module.Page('http://example.com', name='dummy_page',
                            tags=['foo', 'bar'])
    story_set = story_module.StorySet()
    story_set.AddStory(page)
    return story_set

  @classmethod
  def Name(cls):
    return 'BenchmarkFoo'


class BenchmarkDisabled(benchmark.Benchmark):
  """Benchmark disabled for testing."""

  # An empty list means that this benchmark cannot run anywhere.
  SUPPORTED_PLATFORMS = []

  def page_set(self):
    return story_module.StorySet()

  @classmethod
  def Name(cls):
    return 'BenchmarkDisabled'


class PrintBenchmarkListTests(unittest.TestCase):

  def setUp(self):
    self._mock_possible_browser = mock.MagicMock()
    self._mock_possible_browser.browser_type = 'TestBrowser'

  def testPrintBenchmarkListWithNoDisabledBenchmark(self):
    expected_printed_stream = (
        'Available benchmarks for TestBrowser are:\n'
        '  BenchmarkFoo Benchmark foo for testing.\n\n'
        'Pass --browser to list benchmarks for another browser.\n')
    benchmark_list.PrintBenchmarkList([BenchmarkFoo],
                                      self._mock_possible_browser)
    self.assertEquals(expected_printed_stream, sys.stdout.getvalue())


  def testPrintBenchmarkListWithOneDisabledBenchmark(self):
    expected_printed_stream = (
        'Available benchmarks for TestBrowser are:\n'
        '  BenchmarkFoo      Benchmark foo for testing.\n'
        '\n'
        'Not supported benchmarks for TestBrowser are (force run with -d):\n'
        '  BenchmarkDisabled Benchmark disabled for testing.\n\n'
        'Pass --browser to list benchmarks for another browser.\n')

    with mock.patch.object(
        self._mock_possible_browser, 'GetTypExpectationsTags',
        return_value=['all']):
      benchmark_list.PrintBenchmarkList([BenchmarkFoo, BenchmarkDisabled],
                                        self._mock_possible_browser,
                                        stream=sys.stderr)
      self.assertEquals(expected_printed_stream, sys.stderr.getvalue())

  def testPrintBenchmarkListInJSON(self):
    expected_info = {
        'name': BenchmarkFoo.Name(),
        'description': BenchmarkFoo.Description(),
        'enabled': True,
        'supported': True,
        'stories': [
            {
                'name': 'dummy_page',
                'description': '',
                'tags': ['foo', 'bar']
            }
        ]
    }
    actual_info = benchmark_list.GetBenchmarkInfo(
        BenchmarkFoo, self._mock_possible_browser)
    self.assertEquals(expected_info, actual_info)
