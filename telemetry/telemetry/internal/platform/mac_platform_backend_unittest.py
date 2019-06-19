# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest

from mock import MagicMock
from telemetry.core import platform as platform_module
from telemetry.internal.platform import mac_platform_backend
from telemetry.core import os_version
from telemetry import decorators


class MacPlatformBackendTest(unittest.TestCase):
  def testVersionCamparison(self):
    self.assertGreater(os_version.YOSEMITE, os_version.MAVERICKS)
    self.assertGreater(os_version.MAVERICKS, os_version.SNOWLEOPARD)
    self.assertGreater(os_version.LION, os_version.LEOPARD)
    self.assertEqual(os_version.YOSEMITE, 'yosemite')
    self.assertEqual(os_version.MAVERICKS, 'mavericks')
    self.assertEqual('%s2' % os_version.MAVERICKS, 'mavericks2')
    self.assertEqual(''.join([os_version.MAVERICKS, '2']),
                     'mavericks2')
    self.assertEqual(os_version.LION.upper(), 'LION')

  @decorators.Enabled('mac')
  def testGetCPUStats(self):
    platform = platform_module.GetHostPlatform()

    backend = platform._platform_backend # pylint: disable=protected-access

    cpu_stats = backend.GetCpuStats(os.getpid())
    self.assertGreater(cpu_stats['CpuProcessTime'], 0)
    self.assertTrue(cpu_stats.has_key('ContextSwitches'))
    if backend.GetOSVersionName() >= os_version.MAVERICKS:
      self.assertTrue(cpu_stats.has_key('IdleWakeupCount'))

  @decorators.Enabled('mac')
  def testGetSystemLogSmoke(self):
    platform = platform_module.GetHostPlatform()
    self.assertTrue(platform.GetSystemLog())

  @staticmethod
  def _GetTagsToTest(version_number):
    backend = mac_platform_backend.MacPlatformBackend()
    os_version_name_fn = backend.GetOSVersionName
    os_version_detail_str_fn = backend.GetOSVersionDetailString
    ret = None
    try:
      backend.GetOSVersionName = MagicMock(return_value='snowleopard')
      backend.GetOSVersionDetailString = MagicMock(return_value=version_number)
      ret = backend.GetTypExpectationsTags()
    finally:
      backend.GetOSVersionName = os_version_name_fn
      backend.GetOSVersionDetailString = os_version_detail_str_fn
    return ret

  def testGetTypExpectationsTagsIncludesSnowLeopard10_11Tag(self):
    self.assertIn('snowleopard-10.11', self._GetTagsToTest('10.11'))

  def testGetTypExpectationsTagsIncludesSnowLeopard10_12Tag(self):
    self.assertIn('snowleopard-10.12', self._GetTagsToTest('10.12'))
