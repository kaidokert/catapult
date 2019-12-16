# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from telemetry.core import exceptions
from telemetry.internal.backends.chrome import chrome_browser_backend
from telemetry.internal.platform import fuchsia_platform_backend as \
  fuchsia_platform_backend_module

_DEFAULT_PORT = 1234

class FuchsiaBrowserBackend(chrome_browser_backend.ChromeBrowserBackend):
  def __init__(self, fuchsia_platform_backend, browser_options,
               browser_directory, profile_directory):
    assert isinstance(fuchsia_platform_backend,
                      fuchsia_platform_backend_module.FuchsiaPlatformBackend)
    super(FuchsiaBrowserBackend, self).__init__(
        fuchsia_platform_backend,
        browser_options=browser_options,
        browser_directory=browser_directory,
        profile_directory=profile_directory,
        supports_extensions=False,
        supports_tab_control=False)
    self._command_runner = fuchsia_platform_backend.command_runner
    self._browser_process = None

  @property
  def log_file_path(self):
    return None

  def _FindDevToolsPortAndTarget(self):
    return _DEFAULT_PORT, None

  def Start(self, startup_args):
    browser_cmd = [
        'run',
        'fuchsia-pkg://fuchsia.com/web_engine_shell#meta/web_engine_shell.cmx',
        '--remote-debugging-port=%s' % _DEFAULT_PORT,
        'about:blank'
    ]
    self._browser_process = self._command_runner.RunCommandPiped(browser_cmd)
    logging.info('Browser is up!')
    try:
      self.BindDevToolsClient()
    except exceptions.ProcessGoneException:
      self.Close()
      raise

  def GetPid(self):
    return self._browser_process.pid

  def Background(self):
    raise NotImplementedError

  def Close(self):
    super(FuchsiaBrowserBackend, self).Close()

    if self._browser_process:
      logging.info('Shutting down browser process on Fuchsia')
      self._browser_process.kill()
    self._browser_process = None

  def IsBrowserRunning(self):
    return bool(self._browser_process)

  def GetStandardOutput(self):
    raise NotImplementedError()

  def GetStackTrace(self):
    return (False, 'Stack trace is not yet supported on Fuchsia.')

  def SymbolizeMinidump(self, minidump_path):
    raise NotImplementedError()


