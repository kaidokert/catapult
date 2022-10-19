# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import absolute_import
import datetime
import io
import logging
import os
import os.path
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile

import py_utils
from py_utils import cloud_storage
from py_utils import exc_util

from telemetry.core import exceptions
from telemetry.internal.backends.chrome import chrome_browser_backend
from telemetry.internal.backends.chrome import minidump_finder
from telemetry.internal.backends.chrome import desktop_minidump_symbolizer
from telemetry.internal.util import format_for_logging


DEVTOOLS_ACTIVE_PORT_FILE = 'DevToolsActivePort'
UI_DEVTOOLS_ACTIVE_PORT_FILE = 'UIDevToolsActivePort'

class DesktopBrowserBackend(chrome_browser_backend.ChromeBrowserBackend):
  """The backend for controlling a locally-executed browser instance, on Linux,
  Mac or Windows.
  """
  def __init__(self, desktop_platform_backend, browser_options,
               browser_directory, profile_directory,
               executable, flash_path, is_content_shell,
               build_dir=None):
    super().__init__(
        desktop_platform_backend,
        browser_options=browser_options,
        browser_directory=browser_directory,
        profile_directory=profile_directory,
        supports_extensions=not is_content_shell,
        supports_tab_control=not is_content_shell,
        build_dir=build_dir)
    self._executable = executable
    self._flash_path = flash_path
    self._is_content_shell = is_content_shell

    # Initialize fields so that an explosion during init doesn't break in Close.
    self._proc = None
    self._tmp_output_file = None
    # pylint: disable=invalid-name
    self._minidump_path_crashpad_retrieval = {}
    # pylint: enable=invalid-name

    if not self._executable:
      raise Exception('Cannot create browser, no executable found!')

    self._CheckFlashPathExists()
    self._MaybeInitLogFilePath()

  def _MaybeInitLogFilePath(self):
    raise NotImplementedError

  def _CheckFlashPathExists(self):
    raise NotImplementedError


  @property
  def is_logging_enabled(self):
    return self.browser_options.logging_verbosity in [
        self.browser_options.NON_VERBOSE_LOGGING,
        self.browser_options.VERBOSE_LOGGING,
        self.browser_options.SUPER_VERBOSE_LOGGING]

  @property
  def log_file_path(self):
    return self._log_file_path

  def _ExecuteWithOutput(self, cmd):
    raise NotImplementedError

  def IsFile(self, path):
    raise NotImplementedError

  def GetFileContents(self, path):
    raise NotImplementedError

  def GetLines(self, path):
    return self.GetFileContents(path).splitlines()

  @property
  def path(self):
    raise NotImplementedError

  @property
  def processes(self):
    class Process:
      def __init__(self, s):
        # We want to get 3 pieces of information from 'ps aux':
        # - PID of the processes
        # - Type of process (e.g. 'renderer', etc)
        # - RSS of the process
        self.name = re.search(r'--type=(\w+)', s).group(1)
        self.pid = re.search(r' (\d+) ', s).group(1)
        # For RSS, we need a more complicated pattern, since multiple parts of
        # the output are just digits.
        REGEXP = (r'\d+\.\d+'  # %CPU
                  r'\s+'
                  r'\d+\.\d+'  # %MEM
                  r'\s+'
                  r'\d+'       # VSZ
                  r'\s+'
                  r'(\d+)')
        EXAMPLE = ('root           1  0.0  0.0 166760 12228 ?'
                   '        Ss   01:50   0:14 /sbin/init splash')
        assert re.search(REGEXP, EXAMPLE).group(1) == '12228'
        self.rss = re.search(REGEXP, s).group(1)
    tmp = self._ExecuteWithOutput('ps -aux | grep chrome')
    return [Process(line) for line in tmp.split('\n') if '--type=' in line]

  @property
  def supports_uploading_logs(self):
    return (self.browser_options.logs_cloud_bucket and self.log_file_path and
            self.IsFile(self.log_file_path))

  def _GetDevToolsActivePortPath(self):
    return self.path.join(self.profile_directory, DEVTOOLS_ACTIVE_PORT_FILE)

  def _GetDevToolsFileContents(self, file):
    if not self.IsFile(file):
      raise EnvironmentError('DevTools file doest not exist yet')

    # Attempt to avoid reading the file until it's populated.
    # Both stat and open may raise IOError if not ready, the caller will retry.
    lines = self.GetLines(file)
    if lines:
      lines = [line.rstrip() for line in lines]
    if not lines:
      raise EnvironmentError('DevTools file empty')
    return lines

  def _FindDevToolsPortAndTarget(self):
    devtools_file_path = self._GetDevToolsActivePortPath()
    lines = self._GetDevToolsFileContents(devtools_file_path)

    devtools_port = int(lines[0])
    browser_target = lines[1] if len(lines) >= 2 else None
    return devtools_port, browser_target

  def _FindUIDevtoolsPort(self):
    devtools_file_path = self.path.join(self.profile_directory,
                                      UI_DEVTOOLS_ACTIVE_PORT_FILE)
    lines = self._GetDevToolsFileContents(devtools_file_path)
    devtools_port = int(lines[0])
    return devtools_port

  def Start(self, startup_args):
    raise NotImplementedError

  def LogStartCommand(self, command, env):
    """Log the command used to start Chrome.

    In order to keep the length of logs down (see crbug.com/943650),
    we sometimes trim the start command depending on browser_options.
    The command may change between runs, but usually in innocuous ways like
    --user-data-dir changes to a new temporary directory. Some benchmarks
    do use different startup arguments for different stories, but this is
    discouraged. This method could be changed to print arguments that are
    different since the last run if need be.
    """
    formatted_command = format_for_logging.ShellFormat(
        command, trim=self.browser_options.trim_logs)
    logging.info('Starting Chrome: %s\n', formatted_command)
    if not self.browser_options.trim_logs:
      logging.info('Chrome Env: %s', env)

  def BindDevToolsClient(self):
    # In addition to the work performed by the base class, quickly check if
    # the browser process is still alive.
    if not self.IsBrowserRunning():
      raise exceptions.ProcessGoneException(
          'Return code: %d' % self._proc.returncode)
    super().BindDevToolsClient()

  def GetPid(self):
    if self._proc:
      return self._proc.pid
    return None

  def IsBrowserRunning(self):
    return self._proc and self._proc.poll() is None

  def GetStandardOutput(self):
    if not self._tmp_output_file:
      if self.browser_options.show_stdout:
        # This can happen in the case that loading the Chrome binary fails.
        # We print rather than using logging here, because that makes a
        # recursive call to this function.
        print("Can't get standard output with --show-stdout", file=sys.stderr)
      return ''
    self._tmp_output_file.flush()
    try:
      with open(self._tmp_output_file.name) as f:
        return f.read()
    except IOError:
      return ''

  def _IsExecutableStripped(self):
    raise NotImplementedError

  def _GetStackFromMinidump(self, minidump):
    # Create an executable-specific directory if necessary to store symbols
    # for re-use. We purposefully don't clean this up so that future
    # tests can continue to use the same symbols that are unique to the
    # executable.
    symbols_dir = self._CreateExecutableUniqueDirectory('chrome_symbols_')
    dump_symbolizer = desktop_minidump_symbolizer.DesktopMinidumpSymbolizer(
        self.browser.platform.GetOSName(),
        self.browser.platform.GetArchName(),
        self._dump_finder, self.build_dir, symbols_dir=symbols_dir)
    return dump_symbolizer.SymbolizeMinidump(minidump)

  def _GetBrowserExecutablePath(self):
    return self._executable

  def _UploadMinidumpToCloudStorage(self, minidump_path):
    """ Upload minidump_path to cloud storage and return the cloud storage url.
    """
    remote_path = ('minidump-%s-%i.dmp' %
                   (datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                    random.randint(0, 1000000)))
    try:
      return cloud_storage.Insert(cloud_storage.TELEMETRY_OUTPUT, remote_path,
                                  minidump_path)
    except cloud_storage.CloudStorageError as err:
      logging.error('Cloud storage error while trying to upload dump: %s',
                    repr(err))
      return '<Missing link>'

  def SymbolizeMinidump(self, minidump_path):
    return self._InternalSymbolizeMinidump(minidump_path)

  def _InternalSymbolizeMinidump(self, minidump_path):
    cloud_storage_link = self._UploadMinidumpToCloudStorage(minidump_path)

    stack = self._GetStackFromMinidump(minidump_path)
    if not stack:
      error_message = ('Failed to symbolize minidump. Raw stack is uploaded to'
                       ' cloud storage: %s.' % cloud_storage_link)
      return (False, error_message)

    self._symbolized_minidump_paths.add(minidump_path)
    return (True, stack)

  def _TryCooperativeShutdown(self):
    if self.browser.platform.IsCooperativeShutdownSupported():
      # Ideally there would be a portable, cooperative shutdown
      # mechanism for the browser. This seems difficult to do
      # correctly for all embedders of the content API. The only known
      # problem with unclean shutdown of the browser process is on
      # Windows, where suspended child processes frequently leak. For
      # now, just solve this particular problem. See Issue 424024.
      if self.browser.platform.CooperativelyShutdown(self._proc, "chrome"):
        try:
          # Use a long timeout to handle slow Windows debug
          # (see crbug.com/815004)
          # Allow specifying a custom shutdown timeout via the
          # 'CHROME_SHUTDOWN_TIMEOUT' environment variable.
          # TODO(sebmarchand): Remove this now that there's an option to shut
          # down Chrome via Devtools.
          py_utils.WaitFor(
              lambda: not self.IsBrowserRunning(),
              timeout=int(os.getenv('CHROME_SHUTDOWN_TIMEOUT', '15')))
          logging.info('Successfully shut down browser cooperatively')
        except py_utils.TimeoutException as e:
          logging.warning('Failed to cooperatively shutdown. ' +
                          'Proceeding to terminate: ' + str(e))

  def Background(self):
    raise NotImplementedError

  @exc_util.BestEffort
  def Close(self):
    super().Close()

    # First, try to cooperatively shutdown.
    if self.IsBrowserRunning():
      self._TryCooperativeShutdown()

    # Second, try to politely shutdown with SIGINT.  Use SIGINT instead of
    # SIGTERM (or terminate()) here since the browser treats SIGTERM as a more
    # urgent shutdown signal and may not free all resources.
    if self.IsBrowserRunning():
      self._proc.send_signal(signal.SIGINT)
      try:
        py_utils.WaitFor(lambda: not self.IsBrowserRunning(),
                         timeout=int(os.getenv('CHROME_SHUTDOWN_TIMEOUT', 5))
                        )
        self._proc = None
      except py_utils.TimeoutException:
        logging.warning('Failed to gracefully shutdown.')

    # Shutdown aggressively if all above failed.
    if self.IsBrowserRunning():
      logging.warning('Proceed to kill the browser.')
      self._proc.kill()
    self._proc = None

    if self._tmp_output_file:
      self._tmp_output_file.close()
      self._tmp_output_file = None

    # Need a remote minidummp path and these need to be synced.
    if self._tmp_minidump_dir:
      shutil.rmtree(self._tmp_minidump_dir, ignore_errors=True)
      self._tmp_minidump_dir = None
