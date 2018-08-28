# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# pylint: disable=bad-indentation
"""Finds Fuchsia browsers that can be controlled by telemetry."""

import logging

from telemetry.core import platform, fuchsia_interface
from telemetry.internal.backends.chrome import chrome_startup_args
from telemetry.internal.backends.chrome import gpu_compositing_checker
from telemetry.internal.browser import browser
from telemetry.internal.browser import possible_browser

if fuchsia_interface.FUCHSIA_IMPORT_SUCCESS:
  from telemetry.internal.platform import fuchsia_device
  from telemetry.internal.backends.chrome import fuchsia_browser_backend


_FUCHSIA_BROWSER = 'fuchsia_content_shell'


class PossibleFuchsiaBrowser(possible_browser.PossibleBrowser):
  """A launchable fuchsia browser instance."""

  def __init__(self, browser_type, finder_options, fuchsia_platform, is_guest):
    del finder_options
    super(PossibleFuchsiaBrowser, self).__init__(browser_type, 'Zircon', False)
    assert browser_type == _FUCHSIA_BROWSER, (
        'Currently, the Fuchsia browser for catapult is the '
        '{}, not {}'.format(_FUCHSIA_BROWSER, browser_type))
    self._platform = fuchsia_platform
    self._platform_backend = (
        fuchsia_platform._platform_backend) # pylint: disable=protected-access
    self._is_guest = is_guest
    # For now, we can assume that the content_shell binary lives in data
    self.browser_directory = "/data"

  def __repr__(self):
    return 'PossibleFuchsiaBrowser(browser_type=%s)' % self.browser_type

  def _InitPlatformIfNeeded(self):
    self._platform.Initialize()

  @property
  def profile_directory(self):
    # For now, on Fuchsia, the data or tmp directories should be where user data
    # lands.
    return '/data'

  def Create(self, clear_caches=True):
    startup_args = self.GetBrowserStartupArgs(self._browser_options)

    browser_backend = fuchsia_browser_backend.FuchsiaBrowserBackend(
        self._platform_backend, self._browser_options,
        self.browser_directory, self.profile_directory,
        self._is_guest)

    returned_browser = browser.Browser(
        browser_backend, self._platform_backend, startup_args)
    if self._browser_options.assert_gpu_compositing:
      gpu_compositing_checker.AssertGpuCompositingEnabled(
          returned_browser.GetSystemInfo())
    return returned_browser

  def GetBrowserStartupArgs(self, browser_options):
    startup_args = chrome_startup_args.GetFromBrowserOptions(browser_options)
    startup_args.extend(chrome_startup_args.GetReplayArgs(
        self._platform_backend.network_controller_backend))

    startup_args.extend([
        '--enable-smooth-scrolling',
        '--enable-threaded-compositing',
        # Allow devtools to connect to chrome.
        '--remote-debugging-port=0',
        # Open a maximized window.
        '--start-maximized',
        # Disable system startup sound.
        '--ash-disable-system-sounds',
        # Skip user image selection screen, and post login screens.
        '--oobe-skip-postlogin',
        # Disable chrome logging redirect. crbug.com/724273.
        '--disable-logging-redirect'
    ])

    trace_config_file = (self._platform_backend.tracing_controller_backend
                         .GetChromeTraceConfigFile())
    if trace_config_file:
      startup_args.append('--trace-config-file=%s' % trace_config_file)

    return startup_args

  def SupportsOptions(self, browser_options):
    del browser_options
    return True

  def _GetPathsForOsPageCacheFlushing(self):
    return []

def SelectDefaultBrowser(possible_browsers):
  for b in possible_browsers:
    if b.browser_type == _FUCHSIA_BROWSER:
      return b
  return None

def FindAllBrowserTypes(_):
  return [_FUCHSIA_BROWSER]

def FindAllAvailableBrowsers(options, device):
  if not fuchsia_interface.FUCHSIA_IMPORT_SUCCESS:
    return []
  if not isinstance(device, fuchsia_device.FuchsiaDevice):
    return []
  plat = platform.GetPlatformForDevice(device, options)
  return [PossibleFuchsiaBrowser(_FUCHSIA_BROWSER, options, plat, False)]
