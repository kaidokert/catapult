# Copyright 2022 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import absolute_import
import logging
import subprocess as subprocess
import sys
import tempfile

from telemetry.internal.backends.chrome import minidump_finder
from telemetry.internal.backends.chrome import desktop_browser_backend
from telemetry.internal.backends.chrome import desktop_minidump_symbolizer


class RemoteDesktopBrowserBackend(desktop_browser_backend.DesktopBrowserBackend):
  """The backend for controlling a remotely-executed browser instance, on Linux,
  Mac or Windows.
  """
  def __init__(self, remote_platform_backend,
               browser_options,
               browser_directory, profile_directory,
               executable, flash_path, is_content_shell,
               build_dir=None,
               env=None):
    super().__init__(
        remote_platform_backend,
        browser_options=browser_options,
        browser_directory=browser_directory,
        profile_directory=profile_directory,
        executable=executable,
        flash_path=flash_path,
        is_content_shell=is_content_shell,
        build_dir=build_dir)
    self._interface = remote_platform_backend.interface
    self._env = env

  @property
  def path(self):
    return self._interface.path

  def _MaybeInitLogFilePath(self):
    if self.is_logging_enabled:
      self._log_file_path = self._interface.path.join(self._interface.MkdTemp(), 'chrome.log')
    else:
      self._log_file_path = None

  def _CheckFlashPathExists(self):
    if self._flash_path and not self._interface.IsFile(self._flash_path):
      raise RuntimeError('Flash path does not exist: %s' % self._flash_path)

  def _ExecuteWithOutput(self, cmd):
    return self._interface.RunCmdOnDevice(cmd)[0].strip()

  def IsFile(self, path):
    return self._interface.IsFile(path)

  def GetFileContents(self, path):
    return self._interface.GetFileContents(path).strip()

  def Start(self, startup_args):
    assert not self._proc, 'Must call Close() before Start()'

    self._dump_finder = minidump_finder.MinidumpFinder(
        self.browser.platform.GetOSName(), self.browser.platform.GetArchName())

    cmd = [self._executable]
    cmd.extend(startup_args)
    cmd.append('about:blank')
    env = self._env or {}
    env['CHROME_HEADLESS'] = '1'  # Don't upload minidumps.
    env['BREAKPAD_DUMP_LOCATION'] = self._tmp_minidump_dir
    if self.is_logging_enabled:
      sys.stderr.write(
          'Chrome log file will be saved in %s\n' % self.log_file_path)
      env['CHROME_LOG_FILE'] = self.log_file_path
    # Make sure we have predictable language settings that don't differ from the
    # recording.
    for name in ('LC_ALL', 'LC_MESSAGES', 'LANG'):
      encoding = 'en_US.UTF-8'
      if env.get(name, encoding) != encoding:
        logging.warning('Overriding env[%s]=="%s" with default value "%s"',
                        name, env[name], encoding)
      env[name] = 'en_US.UTF-8'

    # Setup DISPLAY.
    if not self._interface.display:
      self._interface.RestartUI(False)

    assert self._interface.display, 'Need DISPLAY available to start browser'
    env['DISPLAY'] = f':{self._interface.display}'

    self.LogStartCommand(cmd, env)

    if not self.browser_options.show_stdout:
      self._tmp_output_file = tempfile.NamedTemporaryFile('w')
      self._proc = self._interface.StartCmdOnDevice(
          cmd, stdout=self._tmp_output_file, stderr=subprocess.STDOUT, env=env)
    else:
      self._proc = self._interface.StartCmdOnDevice(cmd, env=env)

    self.BindDevToolsClient()
    if self._supports_extensions:
      self._WaitForExtensionsToLoad()

  def _IsExecutableStripped(self):
    return False

