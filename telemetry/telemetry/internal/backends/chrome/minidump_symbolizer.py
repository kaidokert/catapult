# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import resource
import shutil
import subprocess
import sys
import tempfile
import threading

from telemetry.internal.util import binary_manager


# Exact number is arbitrary, but we want to make sure that we don't run into
# the soft limit for the number of open files in Mac/Linux if symbolizing
# a minidump from a component build.
_FILES_PER_BREAKPAD_THREAD = 10


class MinidumpSymbolizer(object):
  def __init__(self, os_name, arch_name, dump_finder, build_dir):
    """Abstract class for handling all minidump symbolizing code.

    Args:
      os_name: The OS of the host (if running the test on a device), or the OS
          of the test machine (if running the test locally).
      arch_name: The arch name of the host (if running the test on a device), or
          the OS of the test machine (if running the test locally).
      dump_finder: The minidump_finder.MinidumpFinder instance that is being
          used to find minidumps for the test.
      build_dir: The directory containing Chromium build artifacts to generate
          symbols from.
    """
    self._os_name = os_name
    self._arch_name = arch_name
    self._dump_finder = dump_finder
    self._build_dir = build_dir

  def SymbolizeMinidump(self, minidump):
    """Gets the stack trace from the given minidump.

    Args:
      minidump: the path to the minidump on disk

    Returns:
      None if the stack could not be retrieved for some reason, otherwise a
      string containing the stack trace.
    """
    stackwalk = binary_manager.FetchPath(
        'minidump_stackwalk', self._arch_name, self._os_name)
    if not stackwalk:
      logging.warning('minidump_stackwalk binary not found.')
      return None
    # We only want this logic on linux platforms that are still using breakpad.
    # See crbug.com/667475
    if not self._dump_finder.MinidumpObtainedFromCrashpad(minidump):
      with open(minidump, 'rb') as infile:
        minidump += '.stripped'
        with open(minidump, 'wb') as outfile:
          outfile.write(''.join(infile.read().partition('MDMP')[1:]))

    symbols_dir = tempfile.mkdtemp()
    try:
      self._GenerateBreakpadSymbols(symbols_dir, minidump)
      return subprocess.check_output([stackwalk, minidump, symbols_dir],
                                     stderr=open(os.devnull, 'w'))
    finally:
      shutil.rmtree(symbols_dir)

  def GetSymbolBinaries(self, minidump):
    """Returns a list of paths to binaries where symbols may be located.

    Args:
      minidump: The path to the minidump being symbolized.
    """
    raise NotImplementedError()

  def GetBreakpadPlatformOverride(self):
    """Returns the platform to be passed to generate_breakpad_symbols."""
    return None

  def _GenerateBreakpadSymbols(self, symbols_dir, minidump):
    """Generates Breakpad symbols for use with stackwalking tools.

    Args:
      symbols_dir: The directory where symbols will be written to.
      minidump: The path to the minidump being symbolized.
    """
    logging.info('Dumping Breakpad symbols.')
    generate_breakpad_symbols_command = binary_manager.FetchPath(
        'generate_breakpad_symbols', self._arch_name, self._os_name)
    if not generate_breakpad_symbols_command:
      logging.warning('generate_breakpad_symbols binary not found')
      return

    threads = []
    symbol_binaries = self.GetSymbolBinaries(minidump)
    # Make sure we won't run into the soft limit for open files if there are a
    # lot of paths.
    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    soft_limit = min(
        max(soft_limit, len(symbol_binaries * _FILES_PER_BREAKPAD_THREAD)),
        hard_limit)
    resource.setrlimit(resource.RLIMIT_NOFILE, (soft_limit, hard_limit))
    for binary_path in symbol_binaries:
      cmd = [
          sys.executable,
          generate_breakpad_symbols_command,
          '--binary=%s' % binary_path,
          '--symbols-dir=%s' % symbols_dir,
          '--build-dir=%s' % self._build_dir,
          ]
      if self.GetBreakpadPlatformOverride():
        cmd.append('--platform=%s' % self.GetBreakpadPlatformOverride())

      # Component builds result in a lot of binaries being found by
      # GetSymbolBinaries(), which can result in this taking quite a while,
      # particularly on Mac. So, run everything in parallel.
      t = _SubprocessThread(cmd)
      t.start()
      threads.append(t)

    for t in threads:
      t.join()
      if t.failed:
        logging.error(t.output)
        logging.warning('Failed to execute "%s"', ' '.join(t.cmd))


class _SubprocessThread(threading.Thread):
  """Class to run subprocess.check_output in a separate thread."""
  def __init__(self, cmd):
    super(_SubprocessThread, self).__init__()
    self._cmd = cmd
    self._output = None
    self._failed = False

  @property
  def output(self):
    return self._output

  @property
  def failed(self):
    return self._failed

  @property
  def cmd(self):
    return self._cmd

  def run(self):
    try:
      self._output = subprocess.check_output(self._cmd)
    except subprocess.CalledProcessError as e:
      self._output = e.output
      self._failed = True
