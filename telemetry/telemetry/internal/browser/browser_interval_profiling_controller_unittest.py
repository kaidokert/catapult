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


class FakeWindowsPlatformBackend(object):
  def GetOSName(self):
    return 'windows'


class FakePossibleBrowser(object):
  def __init__(self, platform_backend):
    self._platform_backend = platform_backend

  def AddExtraBrowserArg(self, _):
    pass


class BrowserIntervalProfilingControllerTest(unittest.TestCase):
  def _RunTest(
      self, possible_browser, periods, expected_platform, expected_samples):
    with mock.patch.multiple(
        'telemetry.internal.browser.browser_interval_profiling_controller',
        _AndroidController=mock.DEFAULT,
        _LinuxController=mock.DEFAULT) as mock_classes:
      # 80 characters FTW
      profiling_mod = browser_interval_profiling_controller
      controller = profiling_mod.BrowserIntervalProfilingController(
          possible_browser, '', periods, 1)
      with controller.SamplePeriod('period1', None):
        pass
      with controller.SamplePeriod('period2', None):
        pass

      # Verify that the appropriate platform controller was instantiated.
      self.assertEqual(mock_classes['_AndroidController'].call_count,
                       1 if expected_platform == 'android' else 0)
      self.assertEqual(mock_classes['_LinuxController'].call_count,
                       1 if expected_platform == 'linux' else 0)

      # Verify that samples were collected the expected number of times.
      if controller._platform_controller:
        self.assertEqual(
            controller._platform_controller.SamplePeriod.call_count,
            expected_samples)
      else:
        self.assertEqual(expected_samples, 0)

  def testSupportedAndroid(self):
    possible_browser = FakePossibleBrowser(
        FakeAndroidPlatformBackend(version_codes.OREO))
    self._RunTest(possible_browser, ['period1'], 'android', 1)
    self._RunTest(possible_browser, [], None, 0)

  def testUnsupportedAndroid(self):
    possible_browser = FakePossibleBrowser(
        FakeAndroidPlatformBackend(version_codes.KITKAT))
    self._RunTest(possible_browser, ['period1'], None, 0)
    self._RunTest(possible_browser, [], None, 0)

  def testSupportedDesktop(self):
    possible_browser = FakePossibleBrowser(FakeLinuxPlatformBackend())
    self._RunTest(possible_browser, ['period1', 'period2'], 'linux', 2)
    self._RunTest(possible_browser, [], None, 0)

  def testUnsupportedDesktop(self):
    possible_browser = FakePossibleBrowser(FakeWindowsPlatformBackend())
    self._RunTest(possible_browser, ['period1', 'period2'], None, 0)
    self._RunTest(possible_browser, [], None, 0)
