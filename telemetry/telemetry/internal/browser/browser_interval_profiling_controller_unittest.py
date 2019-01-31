# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import mock

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
  def testProfilingControllerWithIncompatiblePeriods(self):
    profiling_mod = browser_interval_profiling_controller
    with self.assertRaises(Exception) as context:
      profiling_mod.BrowserIntervalProfilingController(
          None, '', ['period1', 'whole_story_run'], 1)
    self.assertTrue('Cannot provide other periods along with'
                    ' whole_story_run.' in context.exception)

  def testSupportedAndroidWithValidSamplePeriod(self):
    possible_browser = FakePossibleBrowser(
        FakeAndroidPlatformBackend(version_codes.OREO))
    profiling_mod = browser_interval_profiling_controller

    with mock.patch.multiple(
        'telemetry.internal.browser.browser_interval_profiling_controller',
        _AndroidController=mock.DEFAULT,
        _LinuxController=mock.DEFAULT) as mock_classes:
      controller = profiling_mod.BrowserIntervalProfilingController(
          possible_browser, '', ['period1', 'period2'], 1)
      with controller.SamplePeriod('period1', None):
        pass
      with controller.SamplePeriod('period2', None):
        pass
      self.assertEqual(mock_classes['_AndroidController'].call_count, 1)
      self.assertEqual(mock_classes['_LinuxController'].call_count, 0)
      self.assertTrue(controller._platform_controller)
      self.assertEqual(
          controller._platform_controller.SamplePeriod.call_count, 2)

  def testSupportedAndroidWithInvalidSamplePeriod(self):
    possible_browser = FakePossibleBrowser(
        FakeAndroidPlatformBackend(version_codes.OREO))
    profiling_mod = browser_interval_profiling_controller

    with mock.patch.multiple(
        'telemetry.internal.browser.browser_interval_profiling_controller',
        _AndroidController=mock.DEFAULT,
        _LinuxController=mock.DEFAULT) as mock_classes:
      controller = profiling_mod.BrowserIntervalProfilingController(
          possible_browser, '', [], 1)
      with controller.SamplePeriod('period1', None):
        pass
      self.assertEqual(mock_classes['_AndroidController'].call_count, 0)
      self.assertEqual(mock_classes['_LinuxController'].call_count, 0)
      self.assertIs(controller._platform_controller, None)

  def testUnsupportedAndroidWithValidSamplePeriod(self):
    possible_browser = FakePossibleBrowser(
        FakeAndroidPlatformBackend(version_codes.KITKAT))
    profiling_mod = browser_interval_profiling_controller

    with mock.patch.multiple(
        'telemetry.internal.browser.browser_interval_profiling_controller',
        _AndroidController=mock.DEFAULT,
        _LinuxController=mock.DEFAULT) as mock_classes:
      controller = profiling_mod.BrowserIntervalProfilingController(
          possible_browser, '', ['period1'], 1)
      with controller.SamplePeriod('period1', None):
        pass
      self.assertEqual(mock_classes['_AndroidController'].call_count, 0)
      self.assertEqual(mock_classes['_LinuxController'].call_count, 0)
      self.assertIs(controller._platform_controller, None)

  def testUnsupportedAndroidWithInvalidSamplePeriod(self):
    possible_browser = FakePossibleBrowser(
        FakeAndroidPlatformBackend(version_codes.KITKAT))
    profiling_mod = browser_interval_profiling_controller

    with mock.patch.multiple(
        'telemetry.internal.browser.browser_interval_profiling_controller',
        _AndroidController=mock.DEFAULT,
        _LinuxController=mock.DEFAULT) as mock_classes:
      controller = profiling_mod.BrowserIntervalProfilingController(
          possible_browser, '', [], 1)
      with controller.SamplePeriod('period1', None):
        pass
      self.assertEqual(mock_classes['_AndroidController'].call_count, 0)
      self.assertEqual(mock_classes['_LinuxController'].call_count, 0)
      self.assertIs(controller._platform_controller, None)

  def testLinuxWithValidAndInvalidSamplePeriods(self):
    possible_browser = FakePossibleBrowser(FakeLinuxPlatformBackend())
    profiling_mod = browser_interval_profiling_controller

    with mock.patch.multiple(
        'telemetry.internal.browser.browser_interval_profiling_controller',
        _AndroidController=mock.DEFAULT,
        _LinuxController=mock.DEFAULT) as mock_classes:
      controller = profiling_mod.BrowserIntervalProfilingController(
          possible_browser, '', ['period1', 'period6'], 1)
      with controller.SamplePeriod('period1', None):
        pass
      with controller.SamplePeriod('period2', None):
        pass
      self.assertEqual(mock_classes['_AndroidController'].call_count, 0)
      self.assertEqual(mock_classes['_LinuxController'].call_count, 1)
      self.assertTrue(controller._platform_controller)
      # Only one sample period, because 'period2' not in periods args to
      # constructor.
      self.assertEqual(
          controller._platform_controller.SamplePeriod.call_count, 1)

  def testLinuxWithInvalidSamplePeriod(self):
    possible_browser = FakePossibleBrowser(FakeLinuxPlatformBackend())
    profiling_mod = browser_interval_profiling_controller

    with mock.patch.multiple(
        'telemetry.internal.browser.browser_interval_profiling_controller',
        _AndroidController=mock.DEFAULT,
        _LinuxController=mock.DEFAULT) as mock_classes:
      controller = profiling_mod.BrowserIntervalProfilingController(
          possible_browser, '', [], 1)
      with controller.SamplePeriod('period1', None):
        pass
      self.assertEqual(mock_classes['_AndroidController'].call_count, 0)
      self.assertEqual(mock_classes['_LinuxController'].call_count, 0)
      self.assertIs(controller._platform_controller, None)

  def testUnsupportedPlatformWithValidSamplePeriod(self):
    possible_browser = FakePossibleBrowser(FakeWindowsPlatformBackend())
    profiling_mod = browser_interval_profiling_controller

    with mock.patch.multiple(
        'telemetry.internal.browser.browser_interval_profiling_controller',
        _AndroidController=mock.DEFAULT,
        _LinuxController=mock.DEFAULT) as mock_classes:
      controller = profiling_mod.BrowserIntervalProfilingController(
          possible_browser, '', ['period1'], 1)
      with controller.SamplePeriod('period1', None):
        pass
      self.assertEqual(mock_classes['_AndroidController'].call_count, 0)
      self.assertEqual(mock_classes['_LinuxController'].call_count, 0)
      self.assertIs(controller._platform_controller, None)

  def testUnsupportedPlatformWithInvalidSamplePeriod(self):
    possible_browser = FakePossibleBrowser(FakeWindowsPlatformBackend())
    profiling_mod = browser_interval_profiling_controller

    with mock.patch.multiple(
        'telemetry.internal.browser.browser_interval_profiling_controller',
        _AndroidController=mock.DEFAULT,
        _LinuxController=mock.DEFAULT) as mock_classes:
      controller = profiling_mod.BrowserIntervalProfilingController(
          possible_browser, '', [], 1)
      with controller.SamplePeriod('period1', None):
        pass
      self.assertEqual(mock_classes['_AndroidController'].call_count, 0)
      self.assertEqual(mock_classes['_LinuxController'].call_count, 0)
      self.assertIs(controller._platform_controller, None)
