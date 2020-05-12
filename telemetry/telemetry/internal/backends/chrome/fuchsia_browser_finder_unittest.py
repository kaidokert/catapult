# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import mock

from telemetry.core import fuchsia_interface
from telemetry.internal.backends.chrome import fuchsia_browser_finder
from telemetry.testing import options_for_unittests


class FuchsiaBrowserFinderTest(unittest.TestCase):
  def setUp(self):
    self.finder_options = options_for_unittests.GetCopy()
    self.fake_platform = mock.Mock()

  def testFilterWebEngineShellArgsCorrectly(self):
    browser_type = 'web-engine-shell'
    not_supported_flag = '--not-supported-flag'
    supported_flag = fuchsia_interface.SUPPORTED_WEB_ENGINE_FLAGS[0]
    browser_options = [not_supported_flag, supported_flag]
    possible_browser = fuchsia_browser_finder.PossibleFuchsiaBrowser(
        browser_type, self.finder_options, self.fake_platform)
    filtered_args = possible_browser.GetBrowserStartupArgs(browser_options)
    self.assertTrue(supported_flag in filtered_args)
    self.assertFalse(not_supported_flag in filtered_args)
