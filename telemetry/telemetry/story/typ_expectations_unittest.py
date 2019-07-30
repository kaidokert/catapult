# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest
import mock

from telemetry import benchmark
from telemetry import story as story_module
from telemetry.story import typ_expectations

class NewStoryExpectationsTest(unittest.TestCase):

  def testDisableBenchmark(self):
    expectations = (
        '# tags: [ all ]\n'
        '# results: [ Skip ]\n'
        'crbug.com/123 [ all ] fake/* [ Skip ]\n')
    with mock.patch.object(benchmark.Benchmark, 'Name', return_value='fake'):
      b = benchmark.Benchmark('fake')
      b.AugmentExpectationsWithParser(expectations)
      b.expectations.SetTags(['All'])
      reason = b._expectations.IsBenchmarkDisabled(None, None)
      self.assertTrue(reason)
      self.assertEqual(reason, 'crbug.com/123')

  def testDisableStoryMultipleConditions(self):
    expectations = (
        '# tags: [ linux win ]\n'
        '# results: [ Skip ]\n'
        '[ linux ] fake/one [ Skip ]\n'
        'crbug.com/123 [ win ] fake/on* [ Skip ]\n')
    for os in ['linux', 'win']:
      with mock.patch.object(
          benchmark.Benchmark, 'Name', return_value='fake'):
        story = mock.MagicMock()
        story.name = 'one'
        story_set = story_module.StorySet()
        story_set._stories.append(story)
        b = benchmark.Benchmark('fake')
        b.AugmentExpectationsWithFile(expectations)
        b.expectations.SetTags([os])
        reason = b._expectations.IsStoryDisabled(story, None, None)
        self.assertTrue(reason)
        if os == 'linux':
          self.assertEqual(reason, 'No reason given')
        else:
          self.assertEqual(reason, 'crbug.com/123')

  def testSerializeStoryExpectations(self):
    test_expectations = '''# tags: [ debug release ]
    # tags: [ amd intel ]
    # results: [ Skip ]
    crbug.com/123 [ intel debug ] fake/* [ Skip ]
    [ amd release ] fake/one [ Skip ]
    '''
    expectations = typ_expectations.StoryExpectations('fake')
    expectations.SetTags(['amd', 'debug'])
    expectations.GetBenchmarkExpectationsFromParser(test_expectations)
    self.assertEqual(expectations.serialize(),
                     {'tags': ['amd', 'debug'],
                      'expectations': {
                          'fake/*': [{'conditions': ['debug', 'intel'],
                                      'line_number': 4,
                                      'reason': 'crbug.com/123'}],
                          'fake/one': [{'conditions': ['amd', 'release'],
                                        'line_number': 5,
                                        'reason': ''}]}})
