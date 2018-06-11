# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from google.appengine.ext import ndb

from dashboard.common import testing_common
from dashboard.common import utils
from dashboard.models import anomaly


class AnomalyTest(testing_common.TestCase):
  """Test case for some functions in anomaly."""

  def testGetTestMetadataKey_Test(self):
    a = anomaly.Anomaly(
        test=ndb.Key('Master', 'm', 'Bot', 'b', 'Test', 't', 'Test', 't'))
    k = a.GetTestMetadataKey()
    self.assertEqual('TestMetadata', k.kind())
    self.assertEqual('m/b/t/t', k.id())
    self.assertEqual('m/b/t/t', utils.TestPath(k))

  def testGetTestMetadataKey_TestMetadata(self):
    a = anomaly.Anomaly(test=utils.TestKey('a/b/c/d'))
    k = a.GetTestMetadataKey()
    self.assertEqual('TestMetadata', k.kind())
    self.assertEqual('a/b/c/d', k.id())
    self.assertEqual('a/b/c/d', utils.TestPath(k))

  def testGetTestMetadataKey_None(self):
    a = anomaly.Anomaly()
    k = a.GetTestMetadataKey()
    self.assertIsNone(k)

  def testGetAnomaliesForTest(self):
    old_style_key1 = utils.OldStyleTestKey('master/bot/test1/metric')
    new_style_key1 = utils.TestMetadataKey('master/bot/test1/metric')
    old_style_key2 = utils.OldStyleTestKey('master/bot/test2/metric')
    new_style_key2 = utils.TestMetadataKey('master/bot/test2/metric')
    anomaly.Anomaly(id="old_1", test=old_style_key1).put()
    anomaly.Anomaly(id="old_1a", test=old_style_key1).put()
    anomaly.Anomaly(id="old_2", test=old_style_key2).put()
    anomaly.Anomaly(id="new_1", test=new_style_key1).put()
    anomaly.Anomaly(id="new_2", test=new_style_key2).put()
    anomaly.Anomaly(id="new_2a", test=new_style_key2).put()
    key1_alerts, _, _ = anomaly.Anomaly.QueryAsync(
        test=new_style_key1).get_result()
    self.assertEqual(
        ['new_1', 'old_1', 'old_1a'], [a.key.id() for a in key1_alerts])
    key2_alerts, _, _ = anomaly.Anomaly.QueryAsync(
        test=old_style_key2).get_result()
    self.assertEqual(
        ['new_2', 'new_2a', 'old_2'], [a.key.id() for a in key2_alerts])
    key2_alerts_limit, _, _ = anomaly.Anomaly.QueryAsync(
        test=old_style_key2, limit=2).get_result()
    self.assertEqual(
        ['new_2', 'new_2a'], [a.key.id() for a in key2_alerts_limit])

  def testComputedTestProperties(self):
    anomaly.Anomaly(
        id="foo",
        test=utils.TestKey('master/bot/benchmark/metric/page')).put()
    a = ndb.Key('Anomaly', 'foo').get()
    self.assertEqual(a.master_name, 'master')
    self.assertEqual(a.bot_name, 'bot')
    self.assertEqual(a.benchmark_name, 'benchmark')


if __name__ == '__main__':
  unittest.main()
