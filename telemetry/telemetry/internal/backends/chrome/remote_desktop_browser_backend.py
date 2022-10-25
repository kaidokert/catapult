# Copyright 2022 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import absolute_import

from telemetry.internal.backends.chrome import desktop_browser_backend


class RemoteDesktopBrowserBackend(desktop_browser_backend.DesktopBrowserBackend
                                 ):
  """The backend for controlling a remotely-executed browser instance, on Linux,
  Mac or Windows.
  """

  def __init__(self,
               remote_platform_backend,
               browser_options,
               browser_directory,
               profile_directory,
               executable,
               flash_path,
               is_content_shell,
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
      self._log_file_path = self._interface.path.join(self._interface.MkdTemp(),
                                                      'chrome.log')
    else:
      self._log_file_path = None

  def _CheckFlashPathExists(self):
    if self._flash_path and not self._interface.IsFile(self._flash_path):
      raise RuntimeError('Flash path does not exist: %s' % self._flash_path)

  def _StartProc(self, cmd, stdout=None, stderr=None, env=None):
    return self._interface.StartCmdOnDevice(
        cmd, stdout=stdout, stderr=stderr, env=env)

  def IsFile(self, path):
    return self._interface.IsFile(path)

  def GetFileContents(self, path):
    return self._interface.GetFileContents(path).strip()

  def Start(self, startup_args):
    if not self._interface.display:
      self._interface.RestartUI(False)
    assert self._interface.display, 'Need DISPLAY available to start browser'
    self._env['DISPLAY'] = f':{self._interface.display}'
    super().Start(startup_args)
