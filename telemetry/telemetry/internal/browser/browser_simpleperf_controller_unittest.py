# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock
import unittest

from devil.android.sdk import version_codes

from telemetry import benchmark
from telemetry.internal.browser import browser_options
from telemetry.page import legacy_page_test
from telemetry.page import Page
from telemetry.testing import fakes


class FakeDevice(object):
  def __init__(self, build_version_sdk):
    super(FakeDevice, self).__init__()
    self.build_version_sdk = build_version_sdk
  def SetProp(self, *_):
    pass

class FakeAndroidPlatformBackend(object):
  def __init__(self, build_version_sdk):
    super(FakeAndroidPlatformBackend, self).__init__()
    self.device = FakeDevice(build_version_sdk)

  def GetOSName(self):
    return 'android'

class FakeLinuxPlatformBackend(object):
  def GetOSName(self):
    return 'linux'

class FakeBrowser(object):
  def __init__(self, platform_backend):
    self._platform_backend = platform_backend

class FakePage(Page):
  def __init__(self):
    super(FakePage, self).__init__(
        url='http://test.org/fake.html',
        name='fake.html')

class FakeTest(legacy_page_test.LegacyPageTest):
  def ValidateAndMeasurePage(self, *_):
    pass

class FakeTab(object):
  def CollectGarbage(self):
    pass
  def Navigate(self, *_):
    pass
  def WaitForDocumentReadyStateToBeInteractiveOrBetter(self, *_):
    pass
  def WaitForFrameToBeDisplayed(self, *_):
    pass

class BrowserSimpleperfControllerTest(unittest.TestCase):
  def setUp(self):
    self.args = []
    self.options = browser_options.BrowserFinderOptions()

  def _RunTest(self, browser, expected_call_count):
    parser = self.options.CreateParser()
    benchmark.AddCommandLineArgs(parser)
    parser.parse_args(self.args)
    shared_state = fakes.FakeSharedPageState(FakeTest(), self.options, None)
    with mock.patch.object(
        shared_state._simpleperf_controller, '_StartSimpleperf',
        new=mock.Mock(return_value=None)) as start_simpleperf_mock:
      shared_state._current_page = FakePage()
      shared_state._current_tab = FakeTab()
      shared_state._simpleperf_controller.DidStartBrowser(browser)
      shared_state._current_page.Run(shared_state)
      self.assertEqual(start_simpleperf_mock.call_count, expected_call_count)

  def testSupportedAndroidNoSimpleperfPeriod(self):
    browser = FakeBrowser(FakeAndroidPlatformBackend(version_codes.OREO))
    self._RunTest(browser, expected_call_count=0)

  def testSupportedAndroidWithSimpleperfPeriod(self):
    self.args.extend(['--simpleperf-period=interactions'])
    browser = FakeBrowser(FakeAndroidPlatformBackend(version_codes.OREO))
    self._RunTest(browser, expected_call_count=1)

  def testUnsupportedAndroidNoSimpleperfPeriod(self):
    browser = FakeBrowser(FakeAndroidPlatformBackend(version_codes.KITKAT))
    self._RunTest(browser, expected_call_count=0)

  def testUnsupportedAndroidWithSimpleperfPeriod(self):
    self.args.extend(['--simpleperf-period=interactions'])
    browser = FakeBrowser(FakeAndroidPlatformBackend(version_codes.KITKAT))
    self._RunTest(browser, expected_call_count=0)

  def testDesktopNoSimpleperfPeriod(self):
    browser = FakeBrowser(FakeLinuxPlatformBackend())
    self._RunTest(browser, expected_call_count=0)

  def testDesktopWithSimpleperfPeriod(self):
    self.args.extend(['--simpleperf-period=interactions'])
    browser = FakeBrowser(FakeLinuxPlatformBackend())
    self._RunTest(browser, expected_call_count=0)
