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

  def _StartProc(self, cmd, stdout=None, stderr=None, env=None):
    return subprocess.Popen(cmd, stdout=stdout, stderr=stderr,
                            env=env)

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


