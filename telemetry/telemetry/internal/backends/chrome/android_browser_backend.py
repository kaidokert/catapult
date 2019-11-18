# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import logging
import os
import posixpath
import shutil

from py_utils import exc_util

from telemetry.core import exceptions
from telemetry.core import util
from telemetry.internal.platform import android_platform_backend as \
  android_platform_backend_module
from telemetry.internal.backends.chrome import android_minidump_symbolizer
from telemetry.internal.backends.chrome import chrome_browser_backend
from telemetry.internal.backends.chrome import minidump_finder
from telemetry.internal.browser import user_agent
from telemetry.internal.results import artifact_logger

from devil.android import app_ui
from devil.android import device_signal
from devil.android.sdk import intent


class AndroidBrowserBackend(chrome_browser_backend.ChromeBrowserBackend):
  """The backend for controlling a browser instance running on Android."""
  DEBUG_ARTIFACT_PREFIX = 'android_debug_info'

  def __init__(self, android_platform_backend, browser_options,
               browser_directory, profile_directory, backend_settings):
    assert isinstance(android_platform_backend,
                      android_platform_backend_module.AndroidPlatformBackend)
    super(AndroidBrowserBackend, self).__init__(
        android_platform_backend,
        browser_options=browser_options,
        browser_directory=browser_directory,
        profile_directory=profile_directory,
        supports_extensions=False,
        supports_tab_control=backend_settings.supports_tab_control)
    self._backend_settings = backend_settings

    # Initialize fields so that an explosion during init doesn't break in Close.
    self._saved_sslflag = ''
    self._app_ui = None

    # Set the debug app if needed.
    self.platform_backend.SetDebugApp(self._backend_settings.package)

  @property
  def log_file_path(self):
    return None

  @property
  def device(self):
    return self.platform_backend.device

  @property
  def supports_app_ui_interactions(self):
    return True

  def GetAppUi(self):
    if self._app_ui is None:
      self._app_ui = app_ui.AppUi(self.device, package=self.package)
    return self._app_ui

  def _StopBrowser(self):
    # Note: it's important to stop and _not_ kill the browser app, since
    # stopping also clears the app state in Android's activity manager.
    self.platform_backend.StopApplication(self._backend_settings.package)

  def Start(self, startup_args):
    assert not startup_args, (
        'Startup arguments for Android should be set during '
        'possible_browser.SetUpEnvironment')
    self._dump_finder = minidump_finder.MinidumpFinder(
        self.browser.platform.GetOSName(), self.browser.platform.GetArchName())
    user_agent_dict = user_agent.GetChromeUserAgentDictFromType(
        self.browser_options.browser_user_agent_type)
    self.device.StartActivity(
        intent.Intent(package=self._backend_settings.package,
                      activity=self._backend_settings.activity,
                      action=None, data='about:blank', category=None,
                      extras=user_agent_dict),
        blocking=True)
    try:
      self.BindDevToolsClient()
    except:
      self.Close()
      raise

  def BindDevToolsClient(self):
    super(AndroidBrowserBackend, self).BindDevToolsClient()
    package = self.devtools_client.GetVersion().get('Android-Package')
    if package is None:
      logging.warning('Could not determine package name from DevTools client.')
    elif package == self._backend_settings.package:
      logging.info('Successfully connected to %s DevTools client', package)
    else:
      raise exceptions.BrowserGoneException(
          self.browser, 'Expected connection to %s but got %s.' % (
              self._backend_settings.package, package))

  def _FindDevToolsPortAndTarget(self):
    devtools_port = self._backend_settings.GetDevtoolsRemotePort(self.device)
    browser_target = None  # Use default
    return devtools_port, browser_target

  def Foreground(self):
    package = self._backend_settings.package
    activity = self._backend_settings.activity
    self.device.StartActivity(
        intent.Intent(package=package,
                      activity=activity,
                      action=None,
                      flags=[intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED]),
        blocking=False)
    # TODO(crbug.com/601052): The following waits for any UI node for the
    # package launched to appear on the screen. When the referenced bug is
    # fixed, remove this workaround and just switch blocking above to True.
    try:
      app_ui.AppUi(self.device).WaitForUiNode(package=package)
    except Exception:
      raise exceptions.BrowserGoneException(
          self.browser,
          'Timed out waiting for browser to come back foreground.')

  def Background(self):
    package = 'org.chromium.push_apps_to_background'
    activity = package + '.PushAppsToBackgroundActivity'
    self.device.StartActivity(
        intent.Intent(
            package=package,
            activity=activity,
            action=None,
            flags=[intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED]),
        blocking=True)

  def ForceJavaHeapGarbageCollection(self):
    # Send USR1 signal to force GC on Chrome processes forked from Zygote.
    # (c.f. crbug.com/724032)
    self.device.KillAll(
        self._backend_settings.package,
        exact=False,  # Send signal to children too.
        signum=device_signal.SIGUSR1,
        as_root=True)

  @property
  def processes(self):
    try:
      zygotes = self.device.ListProcesses('zygote')
      zygote_pids = set(p.pid for p in zygotes)
      assert zygote_pids, 'No Android zygote found'
      processes = self.device.ListProcesses(self._backend_settings.package)
      return [p for p in processes if p.ppid in zygote_pids]
    except Exception as exc:
      # Re-raise as an AppCrashException to get further diagnostic information.
      # In particular we also get the values of all local variables above.
      raise exceptions.AppCrashException(
          self.browser, 'Error getting browser PIDs: %s' % exc)

  def GetPid(self):
    browser_processes = self._GetBrowserProcesses()
    assert len(browser_processes) <= 1, (
        'Found too many browsers: %r' % browser_processes)
    if not browser_processes:
      raise exceptions.BrowserGoneException(self.browser)
    return browser_processes[0].pid

  def _GetBrowserProcesses(self):
    """Return all possible browser processes."""
    package = self._backend_settings.package
    return [p for p in self.processes if p.name == package]

  @property
  def package(self):
    return self._backend_settings.package

  @property
  def activity(self):
    return self._backend_settings.activity

  def __del__(self):
    self.Close()

  @exc_util.BestEffort
  def Close(self):
    super(AndroidBrowserBackend, self).Close()
    self._StopBrowser()
    if self._tmp_minidump_dir:
      shutil.rmtree(self._tmp_minidump_dir, ignore_errors=True)
      self._tmp_minidump_dir = None

  def IsBrowserRunning(self):
    return len(self._GetBrowserProcesses()) > 0

  def GetStandardOutput(self):
    return self.platform_backend.GetStandardOutput()

  def PullMinidumps(self):
    self._PullMinidumpsAndAdjustMtimes()

  def CollectDebugData(self, log_level):
    """Attempts to symbolize all currently unsymbolized minidumps and log them.

    Additionally, collects the following information and stores it as artifacts:
      1. UI state of the device
      2. Logcat
      3. Symbolized logcat
      4. Tombstones

    Args:
      log_level: The logging level to use from the logging module, e.g.
          logging.ERROR.
    """
    # Store additional debug information as artifacts.
    # Include the time in the name to guarantee uniqueness if this happens to be
    # called multiple times in a single test. Formatted as
    # year-month-day-hour-minute-second
    now = datetime.datetime.now()
    suffix = now.strftime('%Y-%m-%d-%H-%M-%S')
    self._StoreUiDumpAsArtifact(suffix)
    self._StoreLogcatAsArtifact(suffix)
    self._StoreTombstonesAsArtifact(suffix)
    super(AndroidBrowserBackend, self).CollectDebugData(
        log_level)

  def GetStackTrace(self):
    return self.platform_backend.GetStackTrace()

  def SymbolizeMinidump(self, minidump_path):
    dump_symbolizer = android_minidump_symbolizer.AndroidMinidumpSymbolizer(
        self._dump_finder, util.GetUsedBuildDirectory())
    stack = dump_symbolizer.SymbolizeMinidump(minidump_path)
    if not stack:
      return (False, 'Failed to symbolize minidump.')
    self._symbolized_minidump_paths.add(minidump_path)
    return (True, stack)

  def _PullMinidumpsAndAdjustMtimes(self):
    """Pulls any minidumps from the device to the host.

    Skips pulling any dumps that have already been pulled. The modification time
    of any pulled dumps will be set to the modification time of the dump on the
    device, offset by any difference in clocks between the device and host.
    """
    # The offset is (device_time - host_time), so a positive value means that
    # the device clock is ahead.
    time_offset = self.platform_backend.GetDeviceHostClockOffset()
    device = self.platform_backend.device

    device_dump_path = posixpath.join(
        self.platform_backend.GetDumpLocation(), 'Crashpad', 'pending')
    device_dumps = device.ListDirectory(device_dump_path)
    for dump_filename in device_dumps:
      host_path = os.path.join(self._tmp_minidump_dir, dump_filename)
      if os.path.exists(host_path):
        continue
      device_path = posixpath.join(device_dump_path, dump_filename)
      device.PullFile(device_path, host_path)
      # Set the local version's modification time to the device's
      # The mtime returned by device_utils.StatPath only has a resolution down
      # to the minute, so we can't use that.
      device_mtime = device.RunShellCommand(
          ['stat', '-c', '%Y', device_path], single_line=True)
      device_mtime = int(device_mtime.strip())
      host_mtime = device_mtime - time_offset
      os.utime(host_path, (host_mtime, host_mtime))

  def _StoreUiDumpAsArtifact(self, suffix):
    ui_dump = self.platform_backend.GetSystemUi().ScreenDump()
    artifact_name = posixpath.join(
        self.DEBUG_ARTIFACT_PREFIX, 'ui_dump-%s.txt' % suffix)
    artifact_logger.CreateArtifact(artifact_name, '\n'.join(ui_dump))

  def _StoreLogcatAsArtifact(self, suffix):
    logcat = self.platform_backend.GetLogCat()
    artifact_name = posixpath.join(
        self.DEBUG_ARTIFACT_PREFIX, 'logcat-%s.txt' % suffix)
    artifact_logger.CreateArtifact(artifact_name, logcat)

    symbolized_logcat = self.platform_backend.SymbolizeLogCat(logcat)
    if symbolized_logcat is None:
      symbolized_logcat = 'Failed to symbolize logcat. Is the script available?'
    artifact_name = posixpath.join(
        self.DEBUG_ARTIFACT_PREFIX, 'symbolized_logcat-%s.txt' % suffix)
    artifact_logger.CreateArtifact(artifact_name, symbolized_logcat)

  def _StoreTombstonesAsArtifact(self, suffix):
    tombstones = self.platform_backend.GetTombstones()
    if tombstones is None:
      tombstones = 'Failed to get tombstones. Is the script available?'
    artifact_name = posixpath.join(
        self.DEBUG_ARTIFACT_PREFIX, 'tombstones-%s.txt' % suffix)
    artifact_logger.CreateArtifact(artifact_name, tombstones)
