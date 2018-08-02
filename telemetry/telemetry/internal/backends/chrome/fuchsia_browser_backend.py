# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import tempfile

from telemetry.internal.backends.chrome import chrome_browser_backend
from telemetry.internal.backends.chrome_inspector import devtools_client_backend


class FuchsiaBrowserBackend(chrome_browser_backend.ChromeBrowserBackend):
  def __init__(self,
               fuchsia_platform_backend,
               browser_options,
               browser_directory,
               profile_directory,
               is_guest):
    # Copied from CrOS. Currently, it is unknown whether Fuchsia will require
    # a custom BrowserOptions subclass. As such, no potentially fatal assertions
    # on the type of the browser options

    # assert browser_options.IsFuchsiaBrowserOptions()
    super(FuchsiaBrowserBackend, self).__init__(
        fuchsia_platform_backend,
        browser_options=browser_options,
        browser_directory=browser_directory,
        profile_directory=profile_directory,
        supports_extensions=not is_guest,
        supports_tab_control=True)
    self._is_guest = is_guest
    self._browser_handle = None
    self._browser_drainer = None
    self._tmp_out_file = None

  @property
  def log_file_path(self):
    return 'tmp/content_shell.log'

  @property
  def pid(self):
    return None

  def BindDevToolsClient(self):
    if self._devtools_client:
      self._devtools_client.Close()
      self._devtools_client = None
    self._devtools_client = devtools_client_backend.GetDevToolsBackEndIfReady(
        self.platform_backend.GetRemotePort(), self, None)

  def Start(self, startup_args, startup_url=None):
    assert not startup_url, 'startup_url not supported by fuchsia backend'

    # Remove the stale file with the devtools port / browser target
    # prior to restarting chrome.
    self.platform_backend.EnsureStart()
    args = startup_args + ['--ozone-backend=headless']

    self._tmp_out_file = tempfile.NamedTemporaryFile('w', 0)
    self._browser_handle = self.platform_backend.RunBrowser(
        args, self._tmp_out_file)

    try:
      self.BindDevToolsClient()
    except:
      self.Close()
      raise

    logging.info('Browser is up!')

  def Background(self):
    raise NotImplementedError()

  def Close(self):
    assert self._browser_handle, "Cannot Close a browser that wasn't opened!"
    if self._browser_handle.poll() is None:
      self._browser_handle.kill()

  def GetStandardOutput(self):
    self._tmp_out_file.flush()
    with open(self._tmp_out_file.name, 'r') as f:
      return f.read()

  def IsBrowserRunning(self):
    if self._browser_handle and self._browser_handle.poll() is None:
      return True
    return False

  def GetStackTrace(self):
    assert self._browser_handle, ("Can't get a stack trace until the browser is"
                                  " started at least once!")
    out, err = self._browser_handle.communicate()
    return True, "Out:\n%s\nErr:\n%s" % (out, err)

  def GetAllUnsymbolizedMinidumpPaths(self):
    pass

  def GetSystemInfo(self):
    pass

  def GetLogFileContents(self):
    return self.platform_backend.ReadFile(self.log_file_path)

  def _DrainBrowserProcessOutput(self):
    self._stdout, self._stderr = self._browser_handle.communicate()
