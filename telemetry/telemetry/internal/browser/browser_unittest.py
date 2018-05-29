# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import posixpath
import re
import shutil
import tempfile
import unittest

from telemetry.core import exceptions
from telemetry import decorators
from telemetry.internal.browser import browser as browser_module
from telemetry.internal.browser import browser_finder
from telemetry.internal.platform import gpu_device
from telemetry.internal.platform import gpu_info
from telemetry.internal.platform import system_info
from telemetry.testing import browser_test_case
from telemetry.testing import options_for_unittests
from telemetry.timeline import tracing_config

from devil.android import app_ui

import mock


class IntentionalException(Exception):
  pass


class BrowserTest(browser_test_case.BrowserTestCase):
  def testBrowserCreation(self):
    self.assertEquals(1, len(self._browser.tabs))

    # Different browsers boot up to different things.
    assert self._browser.tabs[0].url

  @decorators.Enabled('has tabs')
  def testNewCloseTab(self):
    existing_tab = self._browser.tabs[0]
    self.assertEquals(1, len(self._browser.tabs))
    existing_tab_url = existing_tab.url

    new_tab = self._browser.tabs.New()
    self.assertEquals(2, len(self._browser.tabs))
    self.assertEquals(existing_tab.url, existing_tab_url)
    self.assertEquals(new_tab.url, 'about:blank')

    new_tab.Close()
    self.assertEquals(1, len(self._browser.tabs))
    self.assertEquals(existing_tab.url, existing_tab_url)

  def testMultipleTabCalls(self):
    self._browser.tabs[0].Navigate(self.UrlOfUnittestFile('blank.html'))
    self._browser.tabs[0].WaitForDocumentReadyStateToBeInteractiveOrBetter()

  def testTabCallByReference(self):
    tab = self._browser.tabs[0]
    tab.Navigate(self.UrlOfUnittestFile('blank.html'))
    self._browser.tabs[0].WaitForDocumentReadyStateToBeInteractiveOrBetter()

  @decorators.Enabled('has tabs')
  def testCloseReferencedTab(self):
    self._browser.tabs.New()
    tab = self._browser.tabs[0]
    tab.Navigate(self.UrlOfUnittestFile('blank.html'))
    tab.Close()
    self.assertEquals(1, len(self._browser.tabs))

  @decorators.Enabled('has tabs')
  def testForegroundTab(self):
    # Should be only one tab at this stage, so that must be the foreground tab
    original_tab = self._browser.tabs[0]
    self.assertEqual(self._browser.foreground_tab, original_tab)
    new_tab = self._browser.tabs.New()
    # New tab shouls be foreground tab
    self.assertEqual(self._browser.foreground_tab, new_tab)
    # Make sure that activating the background tab makes it the foreground tab
    original_tab.Activate()
    self.assertEqual(self._browser.foreground_tab, original_tab)
    # Closing the current foreground tab should switch the foreground tab to the
    # other tab
    original_tab.Close()
    self.assertEqual(self._browser.foreground_tab, new_tab)

  # This test uses the reference browser and doesn't have access to
  # helper binaries like crashpad_database_util.
  @decorators.Enabled('linux')
  def testGetMinidumpPathOnCrash(self):
    tab = self._browser.tabs[0]
    with self.assertRaises(exceptions.AppCrashException):
      tab.Navigate('chrome://crash', timeout=5)
    crash_minidump_path = self._browser.GetMostRecentMinidumpPath()
    self.assertIsNotNone(crash_minidump_path)

  def testGetSystemInfo(self):
    if not self._browser.supports_system_info:
      logging.warning(
          'Browser does not support getting system info, skipping test.')
      return

    info = self._browser.GetSystemInfo()

    self.assertTrue(isinstance(info, system_info.SystemInfo))
    self.assertTrue(hasattr(info, 'model_name'))
    self.assertTrue(hasattr(info, 'gpu'))
    self.assertTrue(isinstance(info.gpu, gpu_info.GPUInfo))
    self.assertTrue(hasattr(info.gpu, 'devices'))
    self.assertTrue(len(info.gpu.devices) > 0)
    for g in info.gpu.devices:
      self.assertTrue(isinstance(g, gpu_device.GPUDevice))

  def testGetSystemInfoNotCachedObject(self):
    if not self._browser.supports_system_info:
      logging.warning(
          'Browser does not support getting system info, skipping test.')
      return

    info_a = self._browser.GetSystemInfo()
    info_b = self._browser.GetSystemInfo()
    self.assertFalse(info_a is info_b)

  def testSystemInfoModelNameOnMac(self):
    if self._browser.platform.GetOSName() != 'mac':
      self.skipTest('This test is only run on macOS')
      return

    if not self._browser.supports_system_info:
      logging.warning(
          'Browser does not support getting system info, skipping test.')
      return

    info = self._browser.GetSystemInfo()
    model_name_re = r"[a-zA-Z]* [0-9.]*"
    self.assertNotEqual(re.match(model_name_re, info.model_name), None)

  # crbug.com/628836 (CrOS, where system-guest indicates ChromeOS guest)
  # github.com/catapult-project/catapult/issues/3130 (Windows)
  @decorators.Disabled('cros-chrome-guest', 'system-guest', 'chromeos', 'win')
  def testIsTracingRunning(self):
    tracing_controller = self._browser.platform.tracing_controller
    if not tracing_controller.IsChromeTracingSupported():
      return
    self.assertFalse(tracing_controller.is_tracing_running)
    config = tracing_config.TracingConfig()
    config.enable_chrome_trace = True
    tracing_controller.StartTracing(config)
    self.assertTrue(tracing_controller.is_tracing_running)
    tracing_controller.StopTracing()
    self.assertFalse(tracing_controller.is_tracing_running)

  @decorators.Enabled('android')
  def testGetAppUi(self):
    self.assertTrue(self._browser.supports_app_ui_interactions)
    ui = self._browser.GetAppUi()
    self.assertTrue(isinstance(ui, app_ui.AppUi))
    self.assertIsNotNone(ui.WaitForUiNode(resource_id='action_bar_root'))


class DefaultProfileBrowserTest(browser_test_case.BrowserTestCase):
  _profile_files_to_copy = None
  _device_profile_paths = None
  _device_sdcard_paths = None
  _tempdir = None

  @classmethod
  def setUpClass(cls):
    cls._tempdir = tempfile.mkdtemp()
    # Add a few files and directories.
    foo_path = os.path.join(cls._tempdir, 'foo')
    with open(foo_path, 'w') as f:
      f.write('foo_data')

    bar_path = os.path.join(cls._tempdir, 'path', 'to', 'bar')
    os.makedirs(os.path.dirname(bar_path))
    with open(bar_path, 'w') as f:
      f.write('bar_data')

    cls._profile_files_to_copy = [
        (foo_path, 'foo'),
        (bar_path, posixpath.join('path', 'to', 'bar'))]

    super(cls, DefaultProfileBrowserTest).setUpClass()

  @classmethod
  def tearDownClass(cls):
    if cls._tempdir is not None:
      shutil.rmtree(cls._tempdir)
    super(cls, DefaultProfileBrowserTest).tearDownClass()

  @classmethod
  def CustomizeBrowserOptions(cls, options):
    options.profile_files_to_copy = cls._profile_files_to_copy
    options.profile_dir = None

  @classmethod
  def willCreateBrowser(cls):
    profile_dir = cls._possible_browser.profile_directory

    # PushProfile copies to the sdcard first as an optimization. Make sure if
    # BrowserOptions.profile_dir is set to None it will use _default_profile.
    temp_profile_path = posixpath.join(
        posixpath.sep, 'sdcard', 'profile', '_default_profile')

    cls._device_profile_paths = [
        posixpath.join(profile_dir, path)
        for _, path in cls._profile_files_to_copy]
    cls._device_sdcard_paths = [
        posixpath.join(temp_profile_path, path)
        for _, path in cls._profile_files_to_copy]

  @decorators.Enabled('android')
  def testPushDefaultProfile(self):
    device = self._possible_browser._platform_backend.device
    self.assertTrue(device.PathExists(self._device_profile_paths),
                    self._device_profile_paths)
    self.assertTrue(device.PathExists(self._device_sdcard_paths),
                    self._device_sdcard_paths)

class EmptyProfileBrowserTest(browser_test_case.BrowserTestCase):
  _profile_paths = None

  @classmethod
  def CustomizeBrowserOptions(cls, options):
    options.profile_files_to_copy = []
    options.profile_dir = None

  @classmethod
  def willCreateBrowser(cls):
    profile_dir = cls._possible_browser.profile_directory
    device = cls._possible_browser._platform_backend.device
    cls._profile_paths = device.ListDirectory(profile_dir)

  @decorators.Enabled('android')
  def testPushEmptyProfile(self):
    self.assertEqual(1, len(self._profile_paths))
    lib_path = self._profile_paths[0]
    self.assertEqual("lib", posixpath.basename(lib_path))

class CommandLineBrowserTest(browser_test_case.BrowserTestCase):
  @classmethod
  def CustomizeBrowserOptions(cls, options):
    options.AppendExtraBrowserArgs('--user-agent=telemetry')

  def testCommandLineOverriding(self):
    # This test starts the browser with --user-agent=telemetry. This tests
    # whether the user agent is then set.
    t = self._browser.tabs[0]
    t.Navigate(self.UrlOfUnittestFile('blank.html'))
    t.WaitForDocumentReadyStateToBeInteractiveOrBetter()
    self.assertEquals(t.EvaluateJavaScript('navigator.userAgent'),
                      'telemetry')

class DirtyProfileBrowserTest(browser_test_case.BrowserTestCase):
  @classmethod
  def CustomizeBrowserOptions(cls, options):
    options.profile_type = 'small_profile'

  @decorators.Disabled('chromeos')  # crbug.com/243912
  def testDirtyProfileCreation(self):
    self.assertEquals(1, len(self._browser.tabs))


class BrowserLoggingTest(browser_test_case.BrowserTestCase):
  @classmethod
  def CustomizeBrowserOptions(cls, options):
    options.logging_verbosity = options.VERBOSE_LOGGING

  @decorators.Disabled('chromeos', 'android')
  def testLogFileExist(self):
    self.assertTrue(
        os.path.isfile(self._browser._browser_backend.log_file_path))


class BrowserCreationTest(unittest.TestCase):
  def setUp(self):
    self.mock_browser_backend = mock.MagicMock()
    self.mock_platform_backend = mock.MagicMock()
    self.fake_startup_args = ['--foo', '--bar=2']

  def testCleanedUpCalledWhenExceptionRaisedInBrowserCreation(self):
    self.mock_browser_backend.SetBrowser.side_effect = (
        IntentionalException('Boom!'))
    with self.assertRaises(IntentionalException):
      browser_module.Browser(
          self.mock_browser_backend, self.mock_platform_backend,
          self.fake_startup_args)
    self.assertTrue(self.mock_browser_backend.Close.called)

  def testOriginalExceptionNotSwallow(self):
    self.mock_browser_backend.SetBrowser.side_effect = (
        IntentionalException('Boom!'))
    self.mock_platform_backend.WillCloseBrowser.side_effect = (
        IntentionalException('Cannot close browser!'))
    with self.assertRaises(IntentionalException) as context:
      browser_module.Browser(
          self.mock_browser_backend, self.mock_platform_backend,
          self.fake_startup_args)
    self.assertIn('Boom!', context.exception.message)


class TestBrowserCreation(unittest.TestCase):

  def setUp(self):
    self.finder_options = options_for_unittests.GetCopy()
    self.browser_to_create = browser_finder.FindBrowser(self.finder_options)
    self.browser_to_create.platform.network_controller.Open()

  @property
  def browser_options(self):
    return self.finder_options.browser_options

  def tearDown(self):
    self.browser_to_create.platform.network_controller.Close()

  def testCreateWithBrowserSession(self):
    with self.browser_to_create.BrowserSession(self.browser_options) as browser:
      tab = browser.tabs.New()
      tab.Navigate('about:blank')
      self.assertEquals(2, tab.EvaluateJavaScript('1 + 1'))

  def testCreateWithBadOptionsRaises(self):
    with self.assertRaises(AssertionError):
      # It's an error to pass finder_options instead of browser_options.
      with self.browser_to_create.BrowserSession(self.finder_options):
        pass  # Do nothing.

  @decorators.Enabled('linux')
  # TODO(crbug.com/782691): enable this on Win
  # TODO(ashleymarie): Re-enable on mac (BUG=catapult:#3523)
  @decorators.Isolated
  def testBrowserNotLeakingTempFiles(self):
    before_browser_run_temp_dir_content = os.listdir(tempfile.tempdir)
    with self.browser_to_create.BrowserSession(self.browser_options) as browser:
      tab = browser.tabs.New()
      tab.Navigate('about:blank')
      self.assertEquals(2, tab.EvaluateJavaScript('1 + 1'))
    after_browser_run_temp_dir_content = os.listdir(tempfile.tempdir)
    self.assertEqual(before_browser_run_temp_dir_content,
                     after_browser_run_temp_dir_content)

  def testSuccessfullyStartBrowserWithSystemCacheClearOptions(self):
    browser_options = self.browser_options
    browser_options.clear_sytem_cache_for_browser_and_profile_on_start = True
    with self.browser_to_create.BrowserSession(browser_options) as browser:
      tab = browser.tabs.New()
      tab.Navigate('about:blank')
      self.assertEquals(2, tab.EvaluateJavaScript('1 + 1'))
