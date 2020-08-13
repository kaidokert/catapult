# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest
import mock

from telemetry.internal.platform import win_platform_backend

class WinPlatformBackendTest(unittest.TestCase):
  def testTypExpectationsTagsForLaptop(self):
    backend = win_platform_backend.WinPlatformBackend()
    with mock.patch.object(backend, 'GetPcSystemType', return_value='2'):
      tags = backend.GetTypExpectationsTags()
      self.assertIn('win-laptop', tags)
