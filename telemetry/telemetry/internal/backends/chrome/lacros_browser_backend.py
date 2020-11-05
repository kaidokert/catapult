# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import shutil
import thread
import time

from py_utils import exc_util

from telemetry.core import exceptions
from telemetry import decorators
from telemetry.internal.backends.chrome import chrome_browser_backend
from telemetry.internal.backends.chrome import cros_minidump_symbolizer
from telemetry.internal.backends.chrome import minidump_finder
from telemetry.internal.backends.chrome import misc_web_contents_backend
from telemetry.internal.results import artifact_logger
from telemetry.internal.util import format_for_logging

class LaCrOSBrowserBackend(chrome_browser_backend.ChromeBrowserBackend):
  def __init__(self, cros_platform_backend, browser_options,
               browser_directory, profile_directory, is_guest, env,
               cros_browser_backend, build_dir=None):
    """
    Args:
      cros_platform_backend: The cros_platform_backend.CrOSPlatformBackend
          instance to use.
      browser_options: The browser_options.BrowserOptions instance to use.
      browser_directory: A string containing the path to the directory on the
          device where the browser is installed.
      profile_directory: A string containing a path to the directory on the
          device to store browser profile information in.
      is_guest: A boolean indicating whether the browser is being run in guest
          mode or not.
      env: A list of strings containing environment variables to start the
          browser with.
      cros_browser_backend: The CrOs browser LaCrOs is running on top of.
          Some actions (e.g. Close) are further delegated to this.
      build_dir: A string containing a path to the directory on the host that
          the browser was built in, for finding debug artifacts. Can be None if
          the browser was not locally built, or the directory otherwise cannot
          be determined.
    """
    assert browser_options.IsCrosBrowserOptions()
    super(LaCrOSBrowserBackend, self).__init__(
        cros_platform_backend,
        browser_options=browser_options,
        browser_directory=browser_directory,
        profile_directory=profile_directory,
        supports_extensions=not is_guest,
        supports_tab_control=True,
        build_dir=build_dir)
    self._is_guest = is_guest
    self._cri = cros_platform_backend.cri
    self._env = env
    self._devtools_client_os = None
    self._devtools_port_path = self._GetDevToolsActivePortPath()
    self._cros_browser_backend = cros_browser_backend

  @property
  def log_file_path(self):
    return None

  def _GetDevToolsActivePortPath(self):
    return '/usr/local/lacros-chrome/user_data/DevToolsActivePort'

  def _RunCommandAndLog(self, cmd):
    results = self._cri.RunCmdOnDevice(cmd)
    logging.info("stdout: " + results[0])
    logging.info("stderr: " + results[1])

  def _FindDevToolsPortAndTarget(self):
    devtools_file_path = self._GetDevToolsActivePortPath()
    # GetFileContents may rise IOError or OSError, the caller will retry.
    lines = self._cri.GetFileContents(devtools_file_path).splitlines()
    if not lines:
      raise EnvironmentError('DevTools file empty')

    devtools_port = int(lines[0])
    browser_target = lines[1] if len(lines) >= 2 else None
    return devtools_port, browser_target

  def GetPid(self):
    return self._cri.GetChromePid()

  def __del__(self):
    self.Close()

  def _ReformatArg(self, startup_args, arg_name):
    arg_str = '--' + arg_name + '='
    for i in range(len(startup_args)):
      if arg_str in startup_args[i]:
        new_arg = startup_args[i]
        new_arg = new_arg.replace(arg_str, arg_str + "'")
        new_arg = new_arg + "'"
        new_arg = new_arg.replace(';', '\\;')
        new_arg = new_arg.replace(',', '\\,')
        startup_args[i] = new_arg

  def _LaunchLacrosChromeHelper(self, startup_args):
    # Some args need escaping, etc.
    self._ReformatArg(startup_args, 'enable-features')
    self._ReformatArg(startup_args, 'disable-features')
    self._ReformatArg(startup_args, 'force-fieldtrials')
    self._ReformatArg(startup_args, 'force-fieldtrial-params')
    self._ReformatArg(startup_args, 'proxy-bypass-list')

    # LaCrOs doesn't launch reliably, so try a bunch of times.
    for i in range(40):
      time.sleep(1)
      # If lacros-chrome launches successfully,
      # this won't return until something else closes it
      self._RunCommandAndLog(
          ['EGL_PLATFORM=surfaceless',
         'XDG_RUNTIME_DIR=/run/chrome',
         'python',
         '/mojo_connection_lacros_launcher.py',
         '-s', '/tmp/lacros.sock',
         './../usr/local/lacros-chrome/chrome',
         '--ozone-platform=wayland',
         '--user-data-dir=/usr/local/lacros-chrome/user_data',
         '--enable-gpu-rasterization',
         '--enable-oop-rasterization',
         '--lang=en-US',
         '--breakpad-dump-location=/usr/local/lacros-chrome/',
         '--no-sandbox'] + startup_args)
      # This will only exist if launch is successful.
      if self._cri.FileExistsOnDevice(self._GetDevToolsActivePortPath()):
        break

  def LaunchLacrosChrome(self, startup_args):
    thread.start_new_thread(self._LaunchLacrosChromeHelper, (startup_args,))

  def Start(self, startup_args):
    self._cri.OpenConnection()
    # Remove the stale file with the devtools port / browser target
    # prior to restarting chrome.
    self._cri.RmRF(self._GetDevToolsActivePortPath())

    self._dump_finder = minidump_finder.MinidumpFinder(
        self.browser.platform.GetOSName(), self.browser.platform.GetArchName())

    self.LaunchLacrosChrome(startup_args)
    # Wait for lacros-chrome to start
    for i in range(40):
      time.sleep(1)
      if self._cri.FileExistsOnDevice(self._GetDevToolsActivePortPath()):
        print('LaCrOs is up!')
        break

    self.BindDevToolsClient()

  def Background(self):
    raise NotImplementedError

  @exc_util.BestEffort
  def Close(self):
    super(LaCrOSBrowserBackend, self).Close()

    if self._tmp_minidump_dir:
      shutil.rmtree(self._tmp_minidump_dir, ignore_errors=True)
      self._tmp_minidump_dir = None

    # Underlying CrOS browser is responsible for closing the cri
    self._cros_browser_backend.Close()

  def IsBrowserRunning(self):
    raise NotImplementedError

  def GetStandardOutput(self):
    return 'Cannot get standard output on CrOS'

  def PullMinidumps(self):
    if self._cri:
      self._cri.PullDumps(self._tmp_minidump_dir)
    else:
      logging.error(
          'Attempted to pull minidumps without CrOSInterface. Either the '
          'browser is already closed or was never started.')

  def SymbolizeMinidump(self, minidump_path):
    return self._cros_browser_backend.SymbolizeMinidump(minidump_path)

  def CollectDebugData(self, log_level):
    """Collects various information that may be useful for debugging.

    Args:
      log_level: The logging level to use from the logging module, e.g.
          logging.ERROR.

    Returns:
      A debug_data.DebugData object containing the collected data.
    """
    # TODO(b/...): Pull LaCrOs data
    self._cros_browser_backend.CollectDebugData(log_level)

  @property
  def screenshot_timeout(self):
    # Screenshots fail when the screen is off, and we can flakily attempt to
    # capture screenshots on failure when the screen is off. So, retry for a
    # while if we run into that.
    return 15

  @property
  def supports_overview_mode(self): # pylint: disable=invalid-name
    return True

  def EnterOverviewMode(self, timeout):
    self._cros_browser_backend._devtools_client.window_manager_backend.EnterOverviewMode(timeout)

  def ExitOverviewMode(self, timeout):
    self._cros_browser_backend._devtools_client.window_manager_backend.ExitOverviewMode(timeout)

  @property
  @decorators.Cache
  def misc_web_contents_backend(self):
    """Access to chrome://oobe/login page."""
    return self._cros_browser_backend.misc_web_contents_backend

  @property
  def oobe(self):
    return self._cros_browser_backend.misc_web_contents_backend.GetOobe()

  @property
  def oobe_exists(self):
    return self._cros_browser_backend.misc_web_contents_backend.oobe_exists
