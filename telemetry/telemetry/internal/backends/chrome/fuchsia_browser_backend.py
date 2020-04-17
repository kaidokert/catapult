# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import re
import select
import subprocess

from telemetry.core import util
from telemetry.internal.backends.chrome import chrome_browser_backend
from telemetry.internal.backends.chrome import minidump_finder
from telemetry.internal.platform import fuchsia_platform_backend as fuchsia_platform_backend_module

import py_utils


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
    self._devtools_port = None
    self._symbolizer_proc = None
    self._config_dir = fuchsia_platform_backend.config_dir
    self._browser_log = ''

  @property
  def log_file_path(self):
    return None

  def _RunSymbolizer(self, input_file, output_file, build_id_file,
                     llvm_symbolizer_path):
    """Starts a symbolizer process.

    Args:
      input_file: Input file to be symbolized.
      output_file: Output file for symbolizer stdout and stderr.
      build_id_file: Path to the ids.txt file which maps build IDs to
                      unstripped binaries on the filesystem.
      llvm_symbolizer_path: Path to the llvm-symbolizer

    Returns:
      a Popen object for the started process."""
    sdk_root = os.path.join(util.GetCatapultDir(), '..', 'fuchsia-sdk', 'sdk')
    symbolizer = os.path.join(sdk_root, 'tools', 'x64', 'symbolize')
    symbolizer_cmd = [symbolizer,
                      '-ids-rel', '-llvm-symbolizer', llvm_symbolizer_path,
                      '-build-id-dir', os.path.join(sdk_root, '.build-id')]
    symbolizer_cmd.extend(['-ids', build_id_file])

    logging.debug('Running "%s".' % ' '.join(symbolizer_cmd))
    return subprocess.Popen(symbolizer_cmd, stdin=input_file,
                            stdout=output_file, stderr=subprocess.STDOUT,
                            close_fds=True)

  def _FindDevToolsPortAndTarget(self):
    return self._devtools_port, None

  # Symbolize stderr of process and make the symbolized output the new stderr.
  def _StartSymbolizerForProcessIfPossible(self, process, build_id_file):
    llvm_symbolizer_path = os.path.join(
        util.GetCatapultDir(), '..', 'llvm-build',
        'Release+Asserts', 'bin', 'llvm-symbolizer')
    if (self._browser_process and
        os.path.isfile(llvm_symbolizer_path) and
        os.path.isfile(build_id_file)):
      symbolizer_proc = self._RunSymbolizer(
          process.stderr, subprocess.PIPE,
          build_id_file, llvm_symbolizer_path)
      process.stderr = symbolizer_proc.stdout
      return symbolizer_proc
    else:
      logging.info('Symbolization of web_engine_shell is not available. '
                   'Stdout will only contain raw output.')
      return None

  def _ReadDevToolsPort(self, stderr):
    def TryReadingPort(f):
      if not f:
        return None
      line = f.readline()
      tokens = re.search(r'Remote debugging port: (\d+)', line)
      self._browser_log += line
      return int(tokens.group(1)) if tokens else None
    return py_utils.WaitFor(lambda: TryReadingPort(stderr), timeout=60)

  def Start(self, startup_args):
    browser_cmd = [
        'run',
        'fuchsia-pkg://fuchsia.com/web_engine_shell#meta/web_engine_shell.cmx',
        '--remote-debugging-port=0',
        'about:blank'
    ]
    try:
      self._browser_process = self._command_runner.RunCommandPiped(
          browser_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

      browser_id_file = os.path.join(self._config_dir, 'gen', 'fuchsia',
                                     'engine', 'web_engine_shell', 'ids.txt')
      self._symbolizer_proc = self._StartSymbolizerForProcessIfPossible(
          self._browser_process, browser_id_file)
      self._dump_finder = minidump_finder.MinidumpFinder(
          self.browser.platform.GetOSName(),
          self.browser.platform.GetArchName())
      self._devtools_port = self._ReadDevToolsPort(self._browser_process.stderr)
      self.BindDevToolsClient()
    except:
      logging.info('The browser failed to start. Output of the browser: \n%s' %
                   self.GetStandardOutput())
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
    if self._symbolizer_proc:
      self._symbolizer_proc.kill()
    self._browser_process = None

  def IsBrowserRunning(self):
    return bool(self._browser_process)

  def GetStandardOutput(self):
    if self._browser_process:
      # Make sure there is something to read.
      if select.select([self._browser_process.stderr], [], [], 0.0)[0]:
        self._browser_log += self._browser_process.stderr.read()
    return self._browser_log

  def SymbolizeMinidump(self, minidump_path):
    logging.warning('Symbolizing Minidump not supported on Fuchsia.')
    return None
