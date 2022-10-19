# Copyright 2022 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import absolute_import
import io
import logging
import os
import os.path
import re
import subprocess
import sys
import tempfile

from telemetry.core import exceptions
from telemetry.internal.backends.chrome import desktop_browser_backend
from telemetry.internal.backends.chrome import minidump_finder


class LocalDesktopBrowserBackend(desktop_browser_backend.DesktopBrowserBackend):
  """The backend for controlling a locally-executed browser instance, on Linux,
  Mac or Windows.
  """
  def _MaybeInitLogFilePath(self):
    if self.is_logging_enabled:
      self._log_file_path = os.path.join(tempfile.mkdtemp(), 'chrome.log')
    else:
      self._log_file_path = None

  def _CheckFlashPathExists(self):
    if self._flash_path and not os.path.exists(self._flash_path):
      raise RuntimeError('Flash path does not exist: %s' % self._flash_path)

  def _ExecuteWithOutput(self, cmd):
    return subprocess.getoutput(cmd)

  def IsFile(self, path):
    return os.path.isfile(path)

  @property
  def path(self):
    return os.path

  def GetFileContents(self, path):
    with open(path, 'r') as f:
      return f.read()

  @property
  def supports_uploading_logs(self):
    return (self.browser_options.logs_cloud_bucket and self.log_file_path and
            os.path.isfile(self.log_file_path))

  def Start(self, startup_args):
    assert not self._proc, 'Must call Close() before Start()'

    self._dump_finder = minidump_finder.MinidumpFinder(
        self.browser.platform.GetOSName(), self.browser.platform.GetArchName())

    # macOS displays a blocking crash resume dialog that we need to suppress.
    if self.browser.platform.GetOSName() == 'mac':
      # Default write expects either the application name or the
      # path to the application. self._executable has the path to the app
      # with a few other bits tagged on after .app. Thus, we shorten the path
      # to end with .app. If this is ineffective on your mac, please delete
      # the saved state of the browser you are testing on here:
      # /Users/.../Library/Saved\ Application State/...
      # http://stackoverflow.com/questions/20226802
      dialog_path = re.sub(r'\.app\/.*', '.app', self._executable)
      subprocess.check_call([
          'defaults', 'write', '-app', dialog_path, 'NSQuitAlwaysKeepsWindows',
          '-bool', 'false'
      ])

    cmd = [self._executable]
    if self.browser.platform.GetOSName() == 'mac':
      cmd.append('--use-mock-keychain')  # crbug.com/865247
    cmd.extend(startup_args)
    cmd.append('about:blank')
    env = os.environ.copy()
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

    self.LogStartCommand(cmd, env)

    if not self.browser_options.show_stdout:
      self._tmp_output_file = tempfile.NamedTemporaryFile('w')
      self._proc = subprocess.Popen(
          cmd, stdout=self._tmp_output_file, stderr=subprocess.STDOUT, env=env)
    else:
      # There is weird behavior on Windows where stream redirection does not
      # work as expected if we let the subprocess use the defaults. This results
      # in browser logging not being visible on Windows on swarming. Explicitly
      # setting the streams works around this. The except is in case we are
      # being run through typ, whose _TeedStream replaces the default streams.
      # This can't be used for subprocesses since it is all in-memory, and thus
      # does not have a fileno.
      if sys.platform == 'win32':
        try:
          self._proc = subprocess.Popen(
              cmd, stdout=sys.stdout, stderr=sys.stderr, env=env)
        except io.UnsupportedOperation:
          self._proc = subprocess.Popen(
              cmd, stdout=sys.__stdout__, stderr=sys.__stderr__, env=env)
      else:
        self._proc = subprocess.Popen(cmd, env=env)

    self.BindDevToolsClient()
    # browser is foregrounded by default on Windows and Linux, but not Mac.
    if self.browser.platform.GetOSName() == 'mac':
      subprocess.Popen([
          'osascript', '-e',
          ('tell application "%s" to activate' % self._executable)
      ])
    if self._supports_extensions:
      self._WaitForExtensionsToLoad()

  def _IsExecutableStripped(self):
    if self.browser.platform.GetOSName() == 'mac':
      try:
        symbols = subprocess.check_output(['/usr/bin/nm', self._executable])
      except subprocess.CalledProcessError as err:
        logging.warning(
            'Error when checking whether executable is stripped: %s',
            err.output)
        # Just assume that binary is stripped to skip breakpad symbol generation
        # if this check failed.
        return True
      num_symbols = len(symbols.splitlines())
      # We assume that if there are more than 10 symbols the executable is not
      # stripped.
      return num_symbols < 10
    return False
