# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import shutil
import subprocess
import sys
import tempfile

# resource is not available on Windows
if sys.platform != 'win32':
  import resource

from telemetry.internal.util import binary_manager


# Exact number is arbitrary, but we want to make sure that we don't run into
# the soft limit for the number of open files in Mac/Linux if symbolizing
# a minidump from a component build.
_FILES_PER_BREAKPAD_PROCESS = 10


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

    symbol_binaries = self.GetSymbolBinaries(minidump)
    # POSIX OSes have a soft and hard limit on the number of file handles that
    # a process can have open. On some OSes, the soft limit is relatively low
    # (256 for Mac). This becomes problematic when triggering many subprocesses
    # at once, as each subprocess opens several file handles for piping data.
    # When dozens of subprocesses are opened like in the case of dumping
    # symbols from a component build, combined with the file handles that
    # Python already has open, it's pretty easy to hit this soft cap. So,
    # increase the limit to avoid this issue.
    # We don't bother reseting the limit afterwards since it only affects the
    # current process, and there's no downside to allowing Telemetry to open
    # more files.
    if sys.platform != 'win32':
      soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
      soft_limit = min(
          max(soft_limit, len(symbol_binaries * _FILES_PER_BREAKPAD_PROCESS)),
          hard_limit)
      resource.setrlimit(resource.RLIMIT_NOFILE, (soft_limit, hard_limit))
    processes = []
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

      processes.append(subprocess.Popen(
          cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))

    for p in processes:
      stdout, _ = p.communicate()
      if p.returncode:
        logging.error(stdout)
        logging.warning('Failed to execute %s', cmd)
