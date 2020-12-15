# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import ntpath
import os
import posixpath
import stat
import sys
import unittest

import mock
from pyfakefs import fake_filesystem_unittest

from telemetry import decorators
from telemetry.core import exceptions
from telemetry.core import platform
from telemetry.core import util
from telemetry.internal.backends.chrome import desktop_browser_finder
from telemetry.internal.browser import browser_options
from telemetry.internal.platform import desktop_device
from telemetry.testing import system_stub


WINDOWS_PATHEXT = ['.exe', '.bat']


# This file verifies the logic for finding a browser instance on all platforms
# at once. It does so by providing stubs for the OS/sys/subprocess primitives
# that the underlying finding logic usually uses to locate a suitable browser.
# We prefer this approach to having to run the same test on every platform on
# which we want this code to work.

class FindTestBase(fake_filesystem_unittest.TestCase):
  def setUp(self):
    self.setUpPyfakefs()
    self._finder_options = browser_options.BrowserFinderOptions()

  def tearDown(self):
    os.path = self._old_path
    os.name = self._old_name

  @property
  def _files(self):
    return self._catapult_path_stubs.os.path.files

  def DoFindAll(self):
    return desktop_browser_finder.FindAllAvailableBrowsers(
        self._finder_options, desktop_device.DesktopDevice())

  def DoFindAllTypes(self):
    browsers = self.DoFindAll()
    return [b.browser_type for b in browsers]

  def CanFindAvailableBrowsers(self):
    return desktop_browser_finder.CanFindAvailableBrowsers()

  def _SetupPlatformMocks(self, mock_type):
    self.assertIn(mock_type, ['win', 'linux', 'mac'])

    self._win_patcher = mock.patch.object(desktop_browser_finder, 'IsWin')
    self._win_mock = self._win_patcher.start()
    self.addCleanup(self._win_patcher.stop)
    self._linux_patcher = mock.patch.object(desktop_browser_finder, 'IsLinux')
    self._linux_mock = self._linux_patcher.start()
    self.addCleanup(self._linux_patcher.stop)
    self._mac_patcher = mock.patch.object(desktop_browser_finder, 'IsMac')
    self._mac_mock = self._mac_patcher.start()
    self.addCleanup(self._mac_patcher.stop)

    self._environ_patcher = mock.patch.dict(os.environ, {}, clear=True)
    self._environ_mock = self._environ_patcher.start()
    self.addCleanup(self._environ_patcher.stop)

    # The version of mock that Catapult currently uses seems to have issues
    # with mocking module variables, so we monkey patching seems to be the
    # only way to currently do this.
    self._old_path = os.path
    self._old_name = os.name

    if mock_type == 'win':
      self._win_mock.return_value = True
      self._linux_mock.return_value = False
      self._mac_mock.return_value = False
      self.fs.is_windows_fs = True
      os.name = 'nt'
      os.path = ntpath
      os.environ['PATHEXT'] = ';'.join(WINDOWS_PATHEXT)
      self._finder_options.chrome_root = 'C:\\chrome'
    elif mock_type == 'linux':
      self._win_mock.return_value = False
      self._linux_mock.return_value = True
      self._mac_mock.return_value = False
      self.fs.is_windows_fs = False
      os.name = 'posix'
      os.path = posixpath
      self._finder_options.chrome_root = '/chrome'
    else:
      self._win_mock.return_value = False
      self._linux_mock = False
      self._mac_mock.return_value = True
      self.fs.is_windows_fs = True
      os.name = 'posix'
      os.path = posixpath
      self._finder_options.chrome_root = '/chrome'


class WindowsFindSystemTest(FindTestBase):
  def setUp(self):
    super(WindowsFindSystemTest, self).setUp()
    self._SetupPlatformMocks('win')

  def testFindProgramFiles(self):
    if not self.CanFindAvailableBrowsers():
      return

    os.environ['PROGRAMFILES'] = 'C:\\Program Files'
    self.fs.create_file(
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe')
    self.assertIn('system', self.DoFindAllTypes())

  def testFindProgramFilesX86(self):
    if not self.CanFindAvailableBrowsers():
      return

    os.environ['PROGRAMFILES(X86)'] = 'C:\\Program Files(x86)'
    self.fs.create_file(
        'C:\\Program Files(x86)\\Google\\Chrome\\Application\\chrome.exe')
    self.assertIn('system', self.DoFindAllTypes())

  def testFindLocalAppData(self):
    if not self.CanFindAvailableBrowsers():
      return

    os.environ['LOCALAPPDATA'] = 'C:\\Local App Data'
    self.fs.create_file(
        'C:\\Local App Data\\Google\\Chrome\\Application\\chrome.exe')
    self.assertIn('system', self.DoFindAllTypes())


class WindowsFindLocalBuildsTest(FindTestBase):
  def setUp(self):
    super(WindowsFindLocalBuildsTest, self).setUp()
    self._SetupPlatformMocks('win')

  def testFindBuild(self):
    if not self.CanFindAvailableBrowsers():
      return

    self.fs.create_file('C:\\chrome\\build\\Release\\chrome.exe')
    self.assertIn('release', self.DoFindAllTypes())

  def testFindOut(self):
    if not self.CanFindAvailableBrowsers():
      return

    #self._files.append('..\\..\\..\\out\\Release\\chrome.exe')
    self.fs.create_file('C:\\chrome\\out\\Release\\chrome.exe')
    self.assertIn('release', self.DoFindAllTypes())

  def testFindXcodebuild(self):
    if not self.CanFindAvailableBrowsers():
      return

    #self._files.append('..\\..\\..\\xcodebuild\\Release\\chrome.exe')
    self.fs.create_file('C:\\chrome\\xcodebuild\\Release\\chrome.exe')
    self.assertIn('release', self.DoFindAllTypes())


class OSXFindTest(FindTestBase):
  def setUp(self):
    super(OSXFindTest, self).setUp()
    self._finder_stubs.sys.platform = 'darwin'
    self._path_stubs.sys.platform = 'darwin'
    self._util_stubs.sys.platform = 'darwin'
    self._files.append('/Applications/Google Chrome Canary.app/'
                       'Contents/MacOS/Google Chrome Canary')
    self._files.append('/Applications/Google Chrome.app/' +
                       'Contents/MacOS/Google Chrome')
    self._files.append(
        '../../../out/Release/Chromium.app/Contents/MacOS/Chromium')
    self._files.append(
        '../../../out/Debug/Chromium.app/Contents/MacOS/Chromium')
    self._files.append(
        '../../../out/Release/Content Shell.app/Contents/MacOS/Content Shell')
    self._files.append(
        '../../../out/Debug/Content Shell.app/Contents/MacOS/Content Shell')

  def testFindAll(self):
    if not self.CanFindAvailableBrowsers():
      return

    types = self.DoFindAllTypes()
    self.assertEquals(
        set(types),
        set([
            'debug', 'release', 'content-shell-debug', 'content-shell-release',
            'canary', 'system'
        ]))

  def testFindExact(self):
    if not self.CanFindAvailableBrowsers():
      return

    self._files.append(
        '../../../foo1/Chromium.app/Contents/MacOS/Chromium')
    self._finder_options.browser_executable = (
        '../../../foo1/Chromium.app/Contents/MacOS/Chromium')
    types = self.DoFindAllTypes()
    self.assertTrue('exact' in types)

  def testCannotFindExact(self):
    if not self.CanFindAvailableBrowsers():
      return

    self._files.append(
        '../../../foo1/Chromium.app/Contents/MacOS/Chromium')
    self._finder_options.browser_executable = (
        '../../../foo2/Chromium.app/Contents/MacOS/Chromium')
    self.assertRaises(Exception, self.DoFindAllTypes)

class LinuxFindTest(fake_filesystem_unittest.TestCase):

  def setUp(self):
    if not platform.GetHostPlatform().GetOSName() == 'linux':
      self.skipTest('Not running on Linux')
    self.setUpPyfakefs()
    self.fs.create_dir('/usr/bin')

    self._finder_options = browser_options.BrowserFinderOptions()
    self._finder_options.chrome_root = '/src/'

  def CreateBrowser(self, path):
    self.fs.create_file(path)
    os.chmod(path, stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

  def DoFindAll(self):
    return desktop_browser_finder.FindAllAvailableBrowsers(
        self._finder_options, desktop_device.DesktopDevice())

  def DoFindAllTypes(self):
    return [b.browser_type for b in self.DoFindAll()]

  @decorators.Disabled('android')  # http://crbug.com/905359
  def testFindAllWithCheckout(self):
    # CHROMIUM_OUTPUT_DIR affects the outcome of the tests, so temporarily
    # remove it from the environment.
    output_dir_env = os.environ.pop('CHROMIUM_OUTPUT_DIR', None)

    try:
      for target in ['Release', 'Debug']:
        for browser in ['chrome', 'content_shell']:
          self.CreateBrowser('/src/out/%s/%s' % (target, browser))

      self.assertEquals(
          set(self.DoFindAllTypes()),
          {'debug', 'release', 'content-shell-debug', 'content-shell-release'})
    finally:
      if output_dir_env is not None:
        os.environ['CHROMIUM_OUTPUT_DIR'] = output_dir_env

  def testFindAllFailsIfNotExecutable(self):
    self.fs.create_file('/src/out/Release/chrome')

    self.assertFalse(self.DoFindAllTypes())

  @decorators.Disabled('android')  # http://crbug.com/905359
  def testFindWithProvidedExecutable(self):
    self.CreateBrowser('/foo/chrome')
    self._finder_options.browser_executable = '/foo/chrome'
    self.assertIn('exact', self.DoFindAllTypes())

  def testErrorWithNonExistent(self):
    self._finder_options.browser_executable = '/foo/chrome.apk'
    with self.assertRaises(exceptions.PathMissingError) as cm:
      self.DoFindAllTypes()
    self.assertIn('does not exist or is not executable', str(cm.exception))

  def testErrorWithNonExecutable(self):
    self.fs.create_file('/foo/another_browser')
    self._finder_options.browser_executable = '/foo/another_browser'
    with self.assertRaises(exceptions.PathMissingError) as cm:
      self.DoFindAllTypes()
    self.assertIn('does not exist or is not executable', str(cm.exception))

  @decorators.Disabled('android')  # http://crbug.com/905359
  def testFindAllWithInstalled(self):
    official_names = ['chrome', 'chrome-beta', 'chrome-unstable']

    for name in official_names:
      self.CreateBrowser('/opt/google/%s/chrome' % name)

    self.assertEquals(set(self.DoFindAllTypes()), {'stable', 'beta', 'dev'})

  @decorators.Disabled('android')  # http://crbug.com/905359
  def testFindAllSystem(self):
    self.CreateBrowser('/opt/google/chrome/chrome')
    os.symlink('/opt/google/chrome/chrome', '/usr/bin/google-chrome')

    self.assertEquals(set(self.DoFindAllTypes()), {'system', 'stable'})

  @decorators.Disabled('android')  # http://crbug.com/905359
  def testFindAllSystemIsBeta(self):
    self.CreateBrowser('/opt/google/chrome/chrome')
    self.CreateBrowser('/opt/google/chrome-beta/chrome')
    os.symlink('/opt/google/chrome-beta/chrome', '/usr/bin/google-chrome')

    google_chrome = [browser for browser in self.DoFindAll()
                     if browser.browser_type == 'system'][0]
    self.assertEquals('/opt/google/chrome-beta',
                      google_chrome._browser_directory)


class WinFindTest(FindTestBase):
  def setUp(self):
    super(WinFindTest, self).setUp()

    self._finder_stubs.sys.platform = 'win32'
    self._path_stubs.sys.platform = 'win32'
    self._util_stubs.sys.platform = 'win32'
    self._path_stubs.os.local_app_data = 'c:\\Users\\Someone\\AppData\\Local'
    self._files.append('c:\\tmp\\chrome.exe')
    self._files.append('..\\..\\..\\build\\Release\\chrome.exe')
    self._files.append('..\\..\\..\\build\\Debug\\chrome.exe')
    self._files.append('..\\..\\..\\build\\Release\\content_shell.exe')
    self._files.append('..\\..\\..\\build\\Debug\\content_shell.exe')
    self._files.append(self._path_stubs.os.local_app_data + '\\' +
                       'Google\\Chrome\\Application\\chrome.exe')
    self._files.append(self._path_stubs.os.local_app_data + '\\' +
                       'Google\\Chrome SxS\\Application\\chrome.exe')

  def testFindAllGivenDefaults(self):
    if not self.CanFindAvailableBrowsers():
      return

    types = self.DoFindAllTypes()
    self.assertEquals(set(types),
                      set(['debug', 'release',
                           'content-shell-debug', 'content-shell-release',
                           'system', 'canary']))

  def testFindAllWithExact(self):
    if not self.CanFindAvailableBrowsers():
      return

    self._finder_options.browser_executable = 'c:\\tmp\\chrome.exe'
    types = self.DoFindAllTypes()
    self.assertEquals(
        set(types),
        set(['exact',
             'debug', 'release',
             'content-shell-debug', 'content-shell-release',
             'system', 'canary']))

  def testNoErrorWithUnrecognizedExecutableName(self):
    if not self.CanFindAvailableBrowsers():
      return

    self._files.append('c:\\foo\\another_browser.exe')
    self._finder_options.browser_dir = 'c:\\foo\\another_browser.exe'
    self.assertNotIn('exact', self.DoFindAllTypes())
