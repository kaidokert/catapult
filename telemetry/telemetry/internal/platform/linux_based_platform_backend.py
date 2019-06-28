# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from telemetry import decorators
from telemetry.internal.platform import platform_backend


class LinuxBasedPlatformBackend(platform_backend.PlatformBackend):

  """Abstract platform containing functionality shared by all Linux based OSes.

  This includes Android and ChromeOS.

  Subclasses must implement RunCommand, GetFileContents, GetPsOutput, and
  ParseCStateSample."""

  @decorators.Cache
  def GetSystemTotalPhysicalMemory(self):
    meminfo_contents = self.GetFileContents('/proc/meminfo')
    meminfo = self._GetProcFileDict(meminfo_contents)
    if not meminfo:
      return None
    return self._ConvertToBytes(meminfo['MemTotal'])

  def GetFileContents(self, filename):
    raise NotImplementedError()

  def GetPsOutput(self, columns, pid=None):
    raise NotImplementedError()

  def RunCommand(self, cmd):
    """Runs the specified command.

    Args:
        cmd: A list of program arguments or the path string of the program.
    Returns:
        A string whose content is the output of the command.
    """
    raise NotImplementedError()

  @staticmethod
  def ParseCStateSample(sample):
    """Parse a single c-state residency sample.

    Args:
        sample: A sample of c-state residency times to be parsed. Organized as
            a dictionary mapping CPU name to a string containing all c-state
            names, the times in each state, the latency of each state, and the
            time at which the sample was taken all separated by newlines.
            Ex: {'cpu0': 'C0\nC1\n5000\n2000\n20\n30\n1406673171'}

    Returns:
        Dictionary associating a c-state with a time.
    """
    raise NotImplementedError()

  def _ConvertToBytes(self, value):
    return int(value.replace('kB', '')) * 1024

  def _GetProcFileDict(self, contents):
    retval = {}
    for line in contents.splitlines():
      key, value = line.split(':')
      retval[key.strip()] = value.strip()
    return retval
