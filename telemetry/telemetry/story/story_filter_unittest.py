# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import locale
import optparse
import unittest

import mock

from telemetry import story
from telemetry.page import page
from telemetry.story import story_filter as story_filter_module


class FilterTest(unittest.TestCase):

  def setUp(self):
    story_set = story.StorySet()
    self.p1 = page.Page(
        url='file://your/smile/widen.html', page_set=story_set,
        name='MayYour.smile_widen', tags=['tag1', 'tag2'])
    self.p2 = page.Page(
        url='file://share_a/smile/too.html', page_set=story_set,
        name='ShareA.smiles_too', tags=['tag1'])
    self.p3 = page.Page(
        url='file://share_a/smile/too.html', page_set=story_set,
        name='share_a/smile/too.html', tags=['tag2'])
    self.p4 = page.Page(
        url='file://share_a/smile/too.html', page_set=story_set,
        name='\xd1\x83\xd0\xbb\xd1\x8b\xd0\xb1\xd0\xba\xd0\xb0'.decode('utf-8'),
        tags=['tag2'])
    self.pages = [self.p1, self.p2, self.p3, self.p4]

  @staticmethod
  def ProcessCommandLineArgs(parser=None, **kwargs):
    class Options(object):
      def __init__(
          self, story_filter=None, story_filter_exclude=None,
          story_tag_filter=None, story_tag_filter_exclude=None,
          story_shard_begin_index=None,
          story_shard_end_index=None):
        self.story_filter = story_filter
        self.story_filter_exclude = story_filter_exclude
        self.story_tag_filter = story_tag_filter
        self.story_tag_filter_exclude = story_tag_filter_exclude
        self.story_shard_begin_index = (
            story_shard_begin_index)
        self.story_shard_end_index = (
            story_shard_end_index)
    story_filter_module.StoryFilter.ProcessCommandLineArgs(
        parser, Options(**kwargs))

  def assertPagesSelected(self, expected):
    result = story_filter_module.StoryFilter.FilterStorySet(self.pages)
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
      self.ProcessCommandLineArgs(parser=MockParser(), story_filter=u'+')

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
    self.ProcessCommandLineArgs(story_filter=u'smile_widen')
    self.assertPagesSelected([self.p1])

  def testSharedSubstring(self):
    self.ProcessCommandLineArgs(story_filter=u'smile')
    self.assertPagesSelected([self.p1, self.p2, self.p3])

  def testNoMatch(self):
    self.ProcessCommandLineArgs(story_filter=u'frown')
    self.assertPagesSelected([])

  def testExclude(self):
    self.ProcessCommandLineArgs(story_filter_exclude=u'ShareA')
    self.assertPagesSelected([self.p1, self.p3, self.p4])

  def testExcludeTakesPriority(self):
    self.ProcessCommandLineArgs(
        story_filter=u'smile',
        story_filter_exclude=u'wide')
    self.assertPagesSelected([self.p2, self.p3])

  def testNoNameMatchesDisplayName(self):
    self.ProcessCommandLineArgs(story_filter=u'share_a/smile')
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
    self.assertPagesSelected([self.p2, self.p3, self.p4])

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

  @mock.patch.object(locale, 'getpreferredencoding', return_value='1251')
  def testUnicode(self, locale_mock):
    filter_param = '\xd1\x83\xd0\xbb\xd1\x8b'.decode('utf-8').encode('1251')

    parser = optparse.OptionParser()
    story_filter_module.StoryFilter.AddCommandLineArgs(parser)
    options = parser.parse_args(['--story-filter', filter_param])[0]
    story_filter_module.StoryFilter.ProcessCommandLineArgs(parser, options)
    locale_mock.assert_called()
    self.assertPagesSelected([self.p4])
