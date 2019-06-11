# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import os
import unittest

from telemetry import story
from telemetry import page as page_module
from telemetry import value


class TestBase(unittest.TestCase):
  def setUp(self):
    story_set = story.StorySet(base_dir=os.path.dirname(__file__))
    story_set.AddStory(
        page_module.Page("http://www.bar.com/", story_set, story_set.base_dir,
                         name='http://www.bar.com/'))
    story_set.AddStory(
        page_module.Page("http://www.baz.com/", story_set, story_set.base_dir,
                         name='http://www.baz.com/'))
    story_set.AddStory(
        page_module.Page("http://www.foo.com/", story_set, story_set.base_dir,
                         name='http://www.foo.com/'))
    self.story_set = story_set

  @property
  def pages(self):
    return self.story_set.stories

class ValueForTest(value.Value):
  @classmethod
  def MergeLikeValuesFromSamePage(cls, values):
    pass

  @classmethod
  def MergeLikeValuesFromDifferentPages(cls, values):
    pass

  @staticmethod
  def GetJSONTypeName():
    pass

class ValueForAsDictTest(ValueForTest):
  @staticmethod
  def GetJSONTypeName():
    return 'baz'


class ValueTest(TestBase):
  def testCompat(self):
    page0 = self.pages[0]
    page1 = self.pages[0]

    a = value.Value(page0, 'x', 'unit', important=False, description=None,
                    grouping_label='foo')
    b = value.Value(page1, 'x', 'unit', important=False, description=None,
                    grouping_label='foo')
    self.assertTrue(b.IsMergableWith(a))

    a = value.Value(page0, 'x', 'unit', important=False, description=None,
                    grouping_label='foo')
    b = value.Value(page0, 'x', 'unit', important=False, description=None,
                    grouping_label='bar')
    self.assertTrue(b.IsMergableWith(a))

  def testIncompat(self):
    page0 = self.pages[0]

    a = value.Value(page0, 'x', 'unit', important=False, description=None,
                    grouping_label=None)
    b = value.Value(page0, 'x', 'incompatUnit', important=False,
                    grouping_label=None, description=None)
    self.assertFalse(b.IsMergableWith(a))

    a = value.Value(page0, 'x', 'unit', important=False, description=None,
                    grouping_label=None)
    b = value.Value(page0, 'x', 'unit', important=True, description=None,
                    grouping_label=None)
    self.assertFalse(b.IsMergableWith(a))

    a = value.Value(page0, 'x', 'unit', important=False, description=None,
                    grouping_label=None)
    c = ValueForTest(page0, 'x', 'unit', important=True, description=None,
                     grouping_label=None)
    self.assertFalse(c.IsMergableWith(a))

  def testNameMustBeString(self):
    with self.assertRaises(ValueError):
      value.Value(None, 42, 'unit', important=False, description=None,
                  grouping_label=None)

  def testUnitsMustBeString(self):
    with self.assertRaises(ValueError):
      value.Value(None, 'x', 42, important=False, description=None,
                  grouping_label=None)

  def testImportantMustBeBool(self):
    with self.assertRaises(ValueError):
      value.Value(None, 'x', 'unit', important='foo', description=None,
                  grouping_label=None)

  def testDescriptionMustBeStringOrNone(self):
    with self.assertRaises(ValueError):
      value.Value(None, 'x', 'unit', important=False, description=42,
                  grouping_label=None)

  def testGroupingLabelMustBeStringOrNone(self):
    with self.assertRaises(ValueError):
      value.Value(None, 'x', 'unit', important=False, description=None,
                  grouping_label=42)

  def testAsDictBaseKeys(self):
    v = ValueForAsDictTest(None, 'x', 'unit', important=True, description=None,
                           grouping_label='bar')
    d = v.AsDict()

    self.assertEquals(d, {
        'name': 'x',
        'type': 'baz',
        'units': 'unit',
        'important': True,
        'tir_label': 'bar',  # Note: using legacy name for 'grouping_label'.
    })

  def testAsDictWithPage(self):
    page0 = self.pages[0]

    v = ValueForAsDictTest(page0, 'x', 'unit', important=False,
                           description=None, grouping_label=None)
    d = v.AsDict()

    self.assertIn('page_id', d)

  def testAsDictWithoutPage(self):
    v = ValueForAsDictTest(None, 'x', 'unit', important=False, description=None,
                           grouping_label=None)
    d = v.AsDict()

    self.assertNotIn('page_id', d)

  def testAsDictWithDescription(self):
    v = ValueForAsDictTest(None, 'x', 'unit', important=False,
                           description='Some description.',
                           grouping_label=None)
    d = v.AsDict()
    self.assertEqual('Some description.', d['description'])

  def testAsDictWithoutDescription(self):
    v = ValueForAsDictTest(None, 'x', 'unit', important=False, description=None,
                           grouping_label=None)
    self.assertNotIn('description', v.AsDict())

  def testAsDictWithGroupingLabel(self):
    v = ValueForAsDictTest(None, 'x', 'unit', important=False,
                           description='Some description.',
                           grouping_label='foo')
    d = v.AsDict()
    self.assertEqual('foo', d['tir_label'])

  def testAsDictWithoutGroupingLabel(self):
    v = ValueForAsDictTest(None, 'x', 'unit', important=False, description=None,
                           grouping_label=None)
    self.assertNotIn('tir_label', v.AsDict())

  def testMergedGroupingLabelForSameLabel(self):
    v = ValueForTest(None, 'foo', 'ms', False, 'd', 'bar')

    grouping_label = value.MergedGroupingLabel([v, v])
    self.assertEquals(grouping_label, 'bar')

  def testMergedGroupingLabelForDifferentLabels(self):
    v0 = ValueForTest(None, 'foo', 'ms', False, 'd', 'bar')
    v1 = ValueForTest(None, 'foo', 'ms', False, 'd', 'baz')

    grouping_label = value.MergedGroupingLabel([v0, v1])
    self.assertIsNone(grouping_label)
