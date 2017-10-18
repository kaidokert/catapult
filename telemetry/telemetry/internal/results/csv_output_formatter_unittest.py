# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import StringIO
import unittest

import mock

from telemetry import story
from telemetry import benchmark
from telemetry.internal.results import csv_output_formatter
from telemetry.internal.results import page_test_results
from telemetry import page as page_module
from telemetry.value import improvement_direction
from telemetry.value import scalar
from telemetry.value import trace
from tracing.trace_data import trace_data


def _MakeStorySet():
  story_set = story.StorySet(base_dir=os.path.dirname(__file__))
  story_set.AddStory(page_module.Page(
      'http://www.foo.com/', story_set, story_set.base_dir,
      name='http://www.foo.com/'))
  story_set.AddStory(page_module.Page(
      'http://www.bar.com/', story_set, story_set.base_dir,
      name='http://www.bar.com/'))
  return story_set


class CsvOutputFormatterTest(unittest.TestCase):

  def setUp(self):
    self._output = StringIO.StringIO()
    self._story_set = _MakeStorySet()
    self._results = page_test_results.PageTestResults()
    self._formatter = None
    self.MakeFormatter()

  def MakeFormatter(self):
    self._formatter = csv_output_formatter.CsvOutputFormatter(self._output)

  def SimulateBenchmarkRun(self, list_of_page_and_values):
    """Simulate one run of a benchmark, using the supplied values.

    Args:
      list_of_pages_and_values: a list of tuple (page, list of values)
    """
    for page, values in list_of_page_and_values:
      self._results.WillRunPage(page)
      for v in values:
        v.page = page
        self._results.AddValue(v)
      self._results.DidRunPage(page)

  def Format(self):
    self._results.telemetry_info.benchmark_start_epoch = 15e8
    self._results.PopulateHistogramSet(benchmark.BenchmarkMetadata('benchmark'))
    self._formatter.Format(self._results)
    return self._output.getvalue()

  def testSimple(self):
    # Test a simple benchmark with only one value:
    self.SimulateBenchmarkRun([
        (self._story_set[0], [scalar.ScalarValue(
            None, 'foo', 'seconds', 3,
            improvement_direction=improvement_direction.DOWN)])])
    dicts = csv_output_formatter.ReadCsv(self.Format())
    self.assertEqual(1, len(dicts))
    self.assertEqual('foo', dicts[0].pop('name'))
    self.assertEqual('ms', dicts[0].pop('unit'))
    self.assertEqual('3000', dicts[0].pop('avg'))
    self.assertEqual('1', dicts[0].pop('count'))
    self.assertEqual('3000', dicts[0].pop('max'))
    self.assertEqual('3000', dicts[0].pop('min'))
    self.assertEqual('0', dicts[0].pop('std'))
    self.assertEqual('3000', dicts[0].pop('sum'))
    self.assertEqual('', dicts[0].pop('architectures'))
    self.assertEqual('benchmark', dicts[0].pop('benchmarks'))
    self.assertEqual('2017-07-14 02:40:00', dicts[0].pop('benchmarkStart'))
    self.assertEqual('', dicts[0].pop('bots'))
    self.assertEqual('', dicts[0].pop('builds'))
    self.assertEqual('', dicts[0].pop('deviceIds'))
    self.assertEqual('benchmark 2017-07-14 02:40:00',
                     dicts[0].pop('displayLabel'))
    self.assertEqual('', dicts[0].pop('masters'))
    self.assertEqual('', dicts[0].pop('memoryAmounts'))
    self.assertEqual('', dicts[0].pop('osNames'))
    self.assertEqual('', dicts[0].pop('osVersions'))
    self.assertEqual('', dicts[0].pop('productVersions'))
    self.assertEqual('http://www.foo.com/', dicts[0].pop('stories'))
    self.assertEqual('', dicts[0].pop('storysetRepeats'))
    self.assertEqual('', dicts[0].pop('storyTags'))
    self.assertEqual('', dicts[0].pop('traceStart'))
    self.assertEqual('', dicts[0].pop('traceUrls'))
    self.assertEqual(0, len(dicts[0]), dicts[0])

  @mock.patch('py_utils.cloud_storage.Insert')
  def testMultiplePagesAndValues(self, cs_insert_mock):
    cs_insert_mock.return_value = 'https://cloud_storage_url/foo'
    trace_value = trace.TraceValue(
        None, trace_data.CreateTraceDataFromRawData('{"traceEvents": []}'),
        remote_path='rp', upload_bucket='foo', cloud_url='http://google.com')
    trace_value.UploadToCloud()
    self.SimulateBenchmarkRun([
        (self._story_set[0], [
            scalar.ScalarValue(
                None, 'foo', 'seconds', 4,
                improvement_direction=improvement_direction.DOWN)]),
        (self._story_set[1], [
            scalar.ScalarValue(
                None, 'foo', 'seconds', 3.4,
                improvement_direction=improvement_direction.DOWN),
            trace_value,
            scalar.ScalarValue(
                None, 'bar', 'km', 10,
                improvement_direction=improvement_direction.DOWN),
            scalar.ScalarValue(
                None, 'baz', 'count', 5,
                improvement_direction=improvement_direction.DOWN)])])

    dicts = csv_output_formatter.ReadCsv(self.Format())
    dicts.sort(key=lambda d: d['name'] + d['avg'])
    self.assertEqual(4, len(dicts))

    self.assertEqual('bar', dicts[0].pop('name'))
    self.assertEqual('', dicts[0].pop('unit'))
    self.assertEqual('10', dicts[0].pop('avg'))
    self.assertEqual('1', dicts[0].pop('count'))
    self.assertEqual('10', dicts[0].pop('max'))
    self.assertEqual('10', dicts[0].pop('min'))
    self.assertEqual('0', dicts[0].pop('std'))
    self.assertEqual('10', dicts[0].pop('sum'))
    self.assertEqual('', dicts[0].pop('architectures'))
    self.assertEqual('benchmark', dicts[0].pop('benchmarks'))
    self.assertEqual('2017-07-14 02:40:00', dicts[0].pop('benchmarkStart'))
    self.assertEqual('', dicts[0].pop('bots'))
    self.assertEqual('', dicts[0].pop('builds'))
    self.assertEqual('', dicts[0].pop('deviceIds'))
    self.assertEqual('benchmark 2017-07-14 02:40:00',
                     dicts[0].pop('displayLabel'))
    self.assertEqual('', dicts[0].pop('masters'))
    self.assertEqual('', dicts[0].pop('memoryAmounts'))
    self.assertEqual('', dicts[0].pop('osNames'))
    self.assertEqual('', dicts[0].pop('osVersions'))
    self.assertEqual('', dicts[0].pop('productVersions'))
    self.assertEqual('http://www.bar.com/', dicts[0].pop('stories'))
    self.assertEqual('', dicts[0].pop('storysetRepeats'))
    self.assertEqual('', dicts[0].pop('storyTags'))
    self.assertEqual('', dicts[0].pop('traceStart'))
    self.assertEqual('http://google.com', dicts[0].pop('traceUrls'))
    self.assertEqual(0, len(dicts[0]), dicts[0])

    self.assertEqual('baz', dicts[1].pop('name'))
    self.assertEqual('', dicts[1].pop('unit'))
    self.assertEqual('5', dicts[1].pop('avg'))
    self.assertEqual('1', dicts[1].pop('count'))
    self.assertEqual('5', dicts[1].pop('max'))
    self.assertEqual('5', dicts[1].pop('min'))
    self.assertEqual('0', dicts[1].pop('std'))
    self.assertEqual('5', dicts[1].pop('sum'))
    self.assertEqual('', dicts[1].pop('architectures'))
    self.assertEqual('benchmark', dicts[1].pop('benchmarks'))
    self.assertEqual('2017-07-14 02:40:00', dicts[1].pop('benchmarkStart'))
    self.assertEqual('', dicts[1].pop('bots'))
    self.assertEqual('', dicts[1].pop('builds'))
    self.assertEqual('', dicts[1].pop('deviceIds'))
    self.assertEqual('benchmark 2017-07-14 02:40:00',
                     dicts[1].pop('displayLabel'))
    self.assertEqual('', dicts[1].pop('masters'))
    self.assertEqual('', dicts[1].pop('memoryAmounts'))
    self.assertEqual('', dicts[1].pop('osNames'))
    self.assertEqual('', dicts[1].pop('osVersions'))
    self.assertEqual('', dicts[1].pop('productVersions'))
    self.assertEqual('http://www.bar.com/', dicts[1].pop('stories'))
    self.assertEqual('', dicts[1].pop('storysetRepeats'))
    self.assertEqual('', dicts[1].pop('storyTags'))
    self.assertEqual('', dicts[1].pop('traceStart'))
    self.assertEqual('http://google.com', dicts[1].pop('traceUrls'))
    self.assertEqual(0, len(dicts[1]), dicts[1])

    self.assertEqual('foo', dicts[2].pop('name'))
    self.assertEqual('ms', dicts[2].pop('unit'))
    self.assertEqual('3400', dicts[2].pop('avg'))
    self.assertEqual('1', dicts[2].pop('count'))
    self.assertEqual('3400', dicts[2].pop('max'))
    self.assertEqual('3400', dicts[2].pop('min'))
    self.assertEqual('0', dicts[2].pop('std'))
    self.assertEqual('3400', dicts[2].pop('sum'))
    self.assertEqual('', dicts[2].pop('architectures'))
    self.assertEqual('benchmark', dicts[2].pop('benchmarks'))
    self.assertEqual('2017-07-14 02:40:00', dicts[2].pop('benchmarkStart'))
    self.assertEqual('', dicts[2].pop('bots'))
    self.assertEqual('', dicts[2].pop('builds'))
    self.assertEqual('', dicts[2].pop('deviceIds'))
    self.assertEqual('benchmark 2017-07-14 02:40:00',
                     dicts[2].pop('displayLabel'))
    self.assertEqual('', dicts[2].pop('masters'))
    self.assertEqual('', dicts[2].pop('memoryAmounts'))
    self.assertEqual('', dicts[2].pop('osNames'))
    self.assertEqual('', dicts[2].pop('osVersions'))
    self.assertEqual('', dicts[2].pop('productVersions'))
    self.assertEqual('http://www.bar.com/', dicts[2].pop('stories'))
    self.assertEqual('', dicts[2].pop('storysetRepeats'))
    self.assertEqual('', dicts[2].pop('storyTags'))
    self.assertEqual('', dicts[2].pop('traceStart'))
    self.assertEqual('http://google.com', dicts[2].pop('traceUrls'))
    self.assertEqual(0, len(dicts[2]), dicts[2])

    self.assertEqual('foo', dicts[3].pop('name'))
    self.assertEqual('ms', dicts[3].pop('unit'))
    self.assertEqual('4000', dicts[3].pop('avg'))
    self.assertEqual('1', dicts[3].pop('count'))
    self.assertEqual('4000', dicts[3].pop('max'))
    self.assertEqual('4000', dicts[3].pop('min'))
    self.assertEqual('0', dicts[3].pop('std'))
    self.assertEqual('4000', dicts[3].pop('sum'))
    self.assertEqual('', dicts[3].pop('architectures'))
    self.assertEqual('benchmark', dicts[3].pop('benchmarks'))
    self.assertEqual('2017-07-14 02:40:00', dicts[3].pop('benchmarkStart'))
    self.assertEqual('', dicts[3].pop('bots'))
    self.assertEqual('', dicts[3].pop('builds'))
    self.assertEqual('', dicts[3].pop('deviceIds'))
    self.assertEqual('benchmark 2017-07-14 02:40:00',
                     dicts[3].pop('displayLabel'))
    self.assertEqual('', dicts[3].pop('masters'))
    self.assertEqual('', dicts[3].pop('memoryAmounts'))
    self.assertEqual('', dicts[3].pop('osNames'))
    self.assertEqual('', dicts[3].pop('osVersions'))
    self.assertEqual('', dicts[3].pop('productVersions'))
    self.assertEqual('http://www.foo.com/', dicts[3].pop('stories'))
    self.assertEqual('', dicts[3].pop('storysetRepeats'))
    self.assertEqual('', dicts[3].pop('storyTags'))
    self.assertEqual('', dicts[3].pop('traceStart'))
    self.assertEqual('', dicts[3].pop('traceUrls'))
    self.assertEqual(0, len(dicts[3]), dicts[3])
