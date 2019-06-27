# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest
import mock

from telemetry import benchmark
from telemetry import story as story_module


class NewStoryExpectationsTest(unittest.TestCase):

  def testDisableBenchmark(self):
    expectations = (
        '# tags: [ all ]\n'
        '[ all ] fak* [ Skip ]\n')
    with mock.patch.object(benchmark.Benchmark, 'platform_tags', ['all']):
      with mock.patch.object(benchmark.Benchmark, 'Name', return_value='fake'):
        with mock.patch.object(
            benchmark.Benchmark, '_use_new_test_expectations_format', True):
          b = benchmark.Benchmark()
          b.AugmentExpectationsWithParser(expectations)
          reason = b._expectations.IsBenchmarkDisabled(None, None)
          self.assertTrue(reason)
          #todo(rmhasan) Add assertion for reason equal to 'No Reason given'

  def testDisableStoryMultipleConditions(self):
    expectations = (
        '# tags: [ linux win ]\n'
        '[ linux ] fake/one [ Skip ]\n'
        '[ win ] fake/on* [ Skip ]\n')
    for os in ['linux', 'win']:
      with mock.patch.object(benchmark.Benchmark, 'platform_tags', [os]):
        with mock.patch.object(
            benchmark.Benchmark, 'Name', return_value='fake'):
          with mock.patch.object(
              benchmark.Benchmark, '_use_new_test_expectations_format', True):
            story = mock.MagicMock()
            story.name = 'one'
            story_set = story_module.StorySet()
            story_set._stories.append(story)
            b = benchmark.Benchmark()
            b.AugmentExpectationsWithParser(expectations)
            reason = b._expectations.IsStoryDisabled(story, None, None)
            self.assertTrue(reason)
            #todo(rmhasan) Add assertion for reason equal to 'No Reason given'

  def testGetBrokenExpectationsNotMatching(self):
    expectations = (
        '# tags: [ mac linux win ]\n'
        '[ linux ] fake/story1 [ Skip ]\n'
        '[ win ] fake/story [ Skip ]\n'
        '[ mac ] fake2/story2 [ Skip ]\n')
    story = mock.MagicMock()
    story.name = 'story1'
    story_set = story_module.StorySet()
    story_set._stories.append(story)
    with mock.patch.object(benchmark.Benchmark, 'Name', return_value='fake'):
      with mock.patch.object(
          benchmark.Benchmark, '_use_new_test_expectations_format', True):
        b = benchmark.Benchmark()
        b.AugmentExpectationsWithParser(expectations)
        self.assertEqual(b.GetBrokenExpectations(story_set), ['story'])

  def testGetBrokenExpectationsMatching(self):
    story_set = story_module.StorySet()

    def _add_story(name):
      story = mock.MagicMock()
      story.name = name
      story_set._stories.append(story)

    expectations = (
        '# tags: [ mac linux win ]\n'
        '[ linux ] fake/one [ Skip ]\n'
        '[ win ] fake/two [ Skip ]\n'
        '[ mac ] fake1/three [ Skip ]\n')

    _add_story('one')
    _add_story('two')
    with mock.patch.object(benchmark.Benchmark, 'Name', return_value='fake'):
      with mock.patch.object(
          benchmark.Benchmark, '_use_new_test_expectations_format', True):
        b = benchmark.Benchmark()
        b.AugmentExpectationsWithParser(expectations)
        self.assertEqual(b.GetBrokenExpectations(story_set), [])

  def testGetConditionsForDisabledBenchmarkInAsDictOutput(self):
    expectations = (
        '# tags: [ mac linux ]\n'
        '# tags: [ nvidia ]\n'
        '[ mac ] fake* [ Skip ]\n'
        'crbug.com/123 [ linux nvidia ] fake* [ Skip ]\n')
    with mock.patch.object(benchmark.Benchmark, 'Name', return_value='fake'):
      with mock.patch.object(
          benchmark.Benchmark, '_use_new_test_expectations_format', True):
        b = benchmark.Benchmark()
        b.AugmentExpectationsWithParser(expectations)
        self.assertEqual(b._expectations.AsDict(), {
            'platforms': [
                (['mac'], 'No reason given'),
                (['nvidia', 'linux'], 'crbug.com/123')],
            'stories': {}})

  def testGetMultipleConditionsForDisabledStoriesInAsDictOutput(self):
    expectations = (
        '# tags: [ mac linux ]\n'
        '# tags: [ nvidia ]\n'
        '[ mac ] fake/one [ Skip ]\n'
        'crbug.com/123 [ linux nvidia ] fake/one [ Skip ]\n')
    with mock.patch.object(benchmark.Benchmark, 'Name', return_value='fake'):
      with mock.patch.object(
          benchmark.Benchmark, '_use_new_test_expectations_format', True):
        b = benchmark.Benchmark()
        b.AugmentExpectationsWithParser(expectations)
        self.assertEqual(
            b._expectations.AsDict(), {
                'platforms': [],
                'stories': {'one': [
                    (['mac'], 'No reason given'),
                    (['nvidia', 'linux'], 'crbug.com/123')]}})

  def testGetBenchmarkAndStoryDisablingConditionsInAsDictOutput(self):
    expectations = (
        '# tags: [ mac linux ]\n'
        '# tags: [ nvidia ]\n'
        'crbug.com/124 [ mac nvidia ] fake* [ Skip ]\n'
        '[ mac ] fake/one [ Skip ]\n'
        'crbug.com/123 [ linux nvidia ] fake/one [ Skip ]\n'
        'crbug.com/125 [ linux ] fake1/one [ Skip ]\n')
    with mock.patch.object(benchmark.Benchmark, 'Name', return_value='fake'):
      with mock.patch.object(
          benchmark.Benchmark, '_use_new_test_expectations_format', True):
        b = benchmark.Benchmark()
        b.AugmentExpectationsWithParser(expectations)
        self.assertEqual(
            b._expectations.AsDict(), {
                'platforms': [(['mac', 'nvidia'], 'crbug.com/124')],
                'stories': {'one': [
                    (['mac'], 'No reason given'),
                    (['nvidia', 'linux'], 'crbug.com/123')]}})
