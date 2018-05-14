# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock
import unittest

from devil.android.sdk import version_codes

from telemetry.internal.browser import browser_interval_profiling_controller


class FakeDevice(object):
  def __init__(self, build_version_sdk):
    super(FakeDevice, self).__init__()
    self.build_version_sdk = build_version_sdk


class FakeAndroidPlatformBackend(object):
  def __init__(self, build_version_sdk):
    super(FakeAndroidPlatformBackend, self).__init__()
    self.device = FakeDevice(build_version_sdk)

  def GetOSName(self):
    return 'android'


class FakeLinuxPlatformBackend(object):
  def GetOSName(self):
    return 'linux'


class FakePossibleBrowser(object):
  def __init__(self, platform_backend):
    self._platform_backend = platform_backend


class BrowserIntervalProfilingControllerTest(unittest.TestCase):
  def _RunTest(
      self, possible_browser, periods, constructor_count, sample_count):
    with mock.patch(
        'telemetry.internal.browser.browser_interval_profiling_controller'
        '._AndroidController') as android_controller_mock:
      # 80 characters FTW
      profiling_mod = browser_interval_profiling_controller
      controller = profiling_mod.BrowserIntervalProfilingController(
          possible_browser, '', periods, 1)
      with controller.SamplePeriod('period1', None):
        pass
      with controller.SamplePeriod('period2', None):
        pass

      # Verify that the appropriate platform controller was instantiated.
      self.assertEqual(android_controller_mock.call_count, constructor_count)

      # Verify that samples were collected the expected number of times.
      if controller._platform_controller:
        self.assertEqual(
            controller._platform_controller.SamplePeriod.call_count,
            sample_count)
      else:
        self.assertEqual(0, sample_count)

  def testSupportedAndroid(self):
    possible_browser = FakePossibleBrowser(
        FakeAndroidPlatformBackend(version_codes.OREO))
    self._RunTest(possible_browser, ['period1'], 1, 1)
    self._RunTest(possible_browser, [], 0, 0)

  def testUnsupportedAndroid(self):
    possible_browser = FakePossibleBrowser(
        FakeAndroidPlatformBackend(version_codes.KITKAT))
    self._RunTest(possible_browser, ['period1'], 0, 0)
    self._RunTest(possible_browser, [], 0, 0)

  def testUnsupportedDesktop(self):
    possible_browser = FakePossibleBrowser(FakeLinuxPlatformBackend())
    self._RunTest(possible_browser, ['period1', 'period2'], 0, 0)
    self._RunTest(possible_browser, [], 0, 0)
