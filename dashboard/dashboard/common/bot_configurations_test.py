# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from dashboard.common import bot_configurations
from dashboard.common import namespaced_stored_object
from dashboard.common import testing_common


class ConfigTest(testing_common.TestCase):

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

  def testAliases(self):
    namespaced_stored_object.Set(bot_configurations.BOT_CONFIGURATIONS_KEY, {
        'a': {
            'alias': 'b',
        },
        'b': {
            'alias': 'c',
        },
        'd': {
            'alias': 'e',
        },
    })
    aliases = bot_configurations.GetAliasesAsync('c').get_result()
    self.assertEqual(3, len(aliases))
    self.assertIn('a', aliases)
    self.assertIn('b', aliases)
    self.assertIn('c', aliases)
    self.assertNotIn('d', aliases)
    self.assertNotIn('e', aliases)
