# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import mock

from telemetry import story as story_module
from telemetry.page import page
from telemetry.story import story_filter as story_filter_module
from telemetry.testing import fakes


class FakeProjectConfig(object):
  def __init__(self, expectations_file=None):
    self.expectations_files = [expectations_file]


class FilterTest(unittest.TestCase):

  def setUp(self):
    story_set = story_module.StorySet()
    self.p1 = page.Page(
        url='file://your/smile/widen.html', page_set=story_set,
        name='MayYour.smile_widen', tags=['tag1', 'tag2'])
    self.p2 = page.Page(
        url='file://share_a/smile/too.html', page_set=story_set,
        name='ShareA.smiles_too', tags=['tag1'])
    self.p3 = page.Page(
        url='file://share_a/smile/too.html', page_set=story_set,
        name='share_a/smile/too.html', tags=['tag2'])
    self.pages = [self.p1, self.p2, self.p3]

  @staticmethod
  def ProcessCommandLineArgs(parser=None, **kwargs):
    environment = FakeProjectConfig('path')
    story_filter_module.StoryFilter.ProcessCommandLineArgs(
        parser, fakes.FakeParsedArgsForStoryFilter(**kwargs), environment)

  def assertPagesSelected(self, expected):
    result = story_filter_module.StoryFilter.FilterStories(self.pages)
    self.assertEqual(expected, result)

  def testNoFilterMatchesAll(self):
    self.ProcessCommandLineArgs()
    self.assertPagesSelected(self.pages)

  def testBadRegexCallsParserError(self):
    class MockParserException(Exception):
      pass
    class MockParser(object):
      def error(self, _):
        raise MockParserException
    with self.assertRaises(MockParserException):
      self.ProcessCommandLineArgs(parser=MockParser(), story_filter='+')

  def testBadStoryShardArgEnd(self):
    class MockParserException(Exception):
      pass
    class MockParser(object):
      def error(self, _):
        raise MockParserException
    with self.assertRaises(MockParserException):
      self.ProcessCommandLineArgs(
          parser=MockParser(), story_shard_end_index=-1)

  def testBadStoryShardArgEndAndBegin(self):
    class MockParserException(Exception):
      pass
    class MockParser(object):
      def error(self, _):
        raise MockParserException
    with self.assertRaises(MockParserException):
      self.ProcessCommandLineArgs(
          parser=MockParser(), story_shard_end_index=2,
          story_shard_begin_index=3)

  def testUniqueSubstring(self):
    self.ProcessCommandLineArgs(story_filter='smile_widen')
    self.assertPagesSelected([self.p1])

  def testSharedSubstring(self):
    self.ProcessCommandLineArgs(story_filter='smile')
    self.assertPagesSelected(self.pages)

  def testNoMatch(self):
    self.ProcessCommandLineArgs(story_filter='frown')
    self.assertPagesSelected([])

  def testExclude(self):
    self.ProcessCommandLineArgs(story_filter_exclude='ShareA')
    self.assertPagesSelected([self.p1, self.p3])

  def testExcludeTakesPriority(self):
    self.ProcessCommandLineArgs(
        story_filter='smile',
        story_filter_exclude='wide')
    self.assertPagesSelected([self.p2, self.p3])

  def testNoNameMatchesDisplayName(self):
    self.ProcessCommandLineArgs(story_filter='share_a/smile')
    self.assertPagesSelected([self.p3])

  def testNotagMatch(self):
    self.ProcessCommandLineArgs(story_tag_filter='tagX')
    self.assertPagesSelected([])

  def testtagsAllMatch(self):
    self.ProcessCommandLineArgs(story_tag_filter='tag1,tag2')
    self.assertPagesSelected(self.pages)

  def testExcludetagTakesPriority(self):
    self.ProcessCommandLineArgs(
        story_tag_filter='tag1',
        story_tag_filter_exclude='tag2')
    self.assertPagesSelected([self.p2])

  def testStoryShardBegin(self):
    self.ProcessCommandLineArgs(story_shard_begin_index=1)
    self.assertPagesSelected([self.p2, self.p3])

  def testStoryShardEnd(self):
    self.ProcessCommandLineArgs(story_shard_end_index=2)
    self.assertPagesSelected([self.p1, self.p2])

  def testStoryShardBoth(self):
    self.ProcessCommandLineArgs(
        story_shard_begin_index=1,
        story_shard_end_index=2)
    self.assertPagesSelected([self.p2])

  def testStoryShardBeginWraps(self):
    self.ProcessCommandLineArgs(story_shard_begin_index=-1)
    self.assertPagesSelected(self.pages)

  def testStoryShardEndWraps(self):
    self.ProcessCommandLineArgs(story_shard_end_index=5)
    self.assertPagesSelected(self.pages)


class FakeExpectations(object):
  def __init__(self, benchmark_name):
    pass

  def SetTags(self, tags):
    pass


class FakeExpectationsEverythingDisabled(FakeExpectations):
  def IsStoryDisabled(self, story):
    del story
    return 'Story disabled because of reason'


class FakeExpectationsEverythingEnabled(FakeExpectations):
  def IsStoryDisabled(self, story):
    del story
    return ''


class FakeStory(object):
  def __init__(self, name='fake_story_name'):
    self.name = name


class ShouldSkipUnittest(unittest.TestCase):
  @mock.patch('telemetry.story.typ_expectations.StoryExpectations',
              FakeExpectationsEverythingDisabled)
  def testRunDisabledFlag(self):
    options = fakes.FakeParsedArgsForStoryFilter(run_disabled_stories=True)
    environment = FakeProjectConfig()
    story_filter_module.StoryFilter.ProcessCommandLineArgs(
        None, options, environment)
    story_filter = story_filter_module.StoryFilter('fake_benchmark_name', [])
    self.assertFalse(story_filter.ShouldSkip(FakeStory()))

  @mock.patch('telemetry.story.typ_expectations.StoryExpectations',
              FakeExpectationsEverythingDisabled)
  def testDisabledViaExpectations(self):
    options = fakes.FakeParsedArgsForStoryFilter(run_disabled_stories=False)
    environment = FakeProjectConfig()
    story_filter_module.StoryFilter.ProcessCommandLineArgs(
        None, options, environment)
    story_filter = story_filter_module.StoryFilter('fake_benchmark_name', [])
    self.assertTrue(story_filter.ShouldSkip(FakeStory()))

  @mock.patch('telemetry.story.typ_expectations.StoryExpectations',
              FakeExpectationsEverythingEnabled)
  def testEnabledViaExpectations(self):
    options = fakes.FakeParsedArgsForStoryFilter(run_disabled_stories=False)
    environment = FakeProjectConfig()
    story_filter_module.StoryFilter.ProcessCommandLineArgs(
        None, options, environment)
    story_filter = story_filter_module.StoryFilter('fake_benchmark_name', [])
    self.assertFalse(story_filter.ShouldSkip(FakeStory()))
