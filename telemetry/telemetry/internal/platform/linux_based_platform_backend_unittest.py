# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
import unittest

# The pylint in use is a older version that will consider using io.open() as
# refining builtin functions. This is fixed in a lower version:
#   https://github.com/PyCQA/pylint/issues/464
# For now, we will skip the check for python 3 conversion.
if sys.version_info.major > 2:
  from io import open  # pylint: disable=redefined-builtin

from telemetry.core import util
from telemetry.internal.platform import linux_based_platform_backend


class TestLinuxBackend(linux_based_platform_backend.LinuxBasedPlatformBackend):

  # pylint: disable=abstract-method

  def __init__(self):
    super(TestLinuxBackend, self).__init__()
    self._mock_files = {}

  def SetMockFile(self, filename, output):
    self._mock_files[filename] = output

  def GetFileContents(self, filename):
    return self._mock_files[filename]


class LinuxBasedPlatformBackendTest(unittest.TestCase):

  def SetMockFileInBackend(self, backend, real_file, mock_file):
    with open(os.path.join(util.GetUnittestDataDir(), real_file)) as f:
      backend.SetMockFile(mock_file, f.read())

  def testGetSystemTotalPhysicalMemory(self):
    backend = TestLinuxBackend()
    self.SetMockFileInBackend(backend, 'proc_meminfo', '/proc/meminfo')
    result = backend.GetSystemTotalPhysicalMemory()
    # 67479191552 == MemTotal * 1024
    self.assertEquals(result, 67479191552)
