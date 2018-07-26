# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from dashboard.common import namespaced_stored_object
from dashboard.pinpoint.models import bot_configurations
from dashboard.pinpoint import test


class ConfigTest(test.TestCase):

  def setUp(self):
    super(ConfigTest, self).setUp()

    namespaced_stored_object.Set(bot_configurations.BOT_CONFIGURATIONS_KEY, {
        'chromium-rel-mac11-pro': {'alias': 'mac-11-perf'},
        'mac-11-perf': {'arg': 'value'},
    })

  def testGet(self):
    actual = bot_configurations.Get('mac-11-perf')
    expected = {'arg': 'value'}
    self.assertEqual(actual, expected)

  def testGetWithAlias(self):
    actual = bot_configurations.Get('chromium-rel-mac11-pro')
    expected = {'arg': 'value'}
    self.assertEqual(actual, expected)

  def testList(self):
    actual = bot_configurations.List()
    expected = ['mac-11-perf']
    self.assertEqual(actual, expected)

  def testAliaseses(self):
    namespaced_stored_object.Set(bot_configurations.BOT_CONFIGURATIONS_KEY, {
        'a': {
            'alias': 'b',
        },
        'c': {
            'alias': 'b',
        },
    })
    aliaseses = bot_configurations.AliasesesAsync().get_result()
    self.assertEqual(1, len(aliaseses))
    self.assertEqual(3, len(aliaseses[0]))
    self.assertIn('a', aliaseses[0])
    self.assertIn('b', aliaseses[0])
    self.assertIn('c', aliaseses[0])
