# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from telemetry.story import shared_state
from telemetry.testing import fakes
from telemetry.util import wpr_modes

class SharedStateTests(unittest.TestCase):
  def setUp(self):
    self.options = fakes.CreateBrowserFinderOptions()
    self.options.use_live_sites = False

  def testUseLiveSitesFlagSet(self):
    self.options.use_live_sites = True
    run_state = shared_state.SharedState(None, self.options, None)
    self.assertEqual(run_state.wpr_mode, wpr_modes.WPR_OFF)

  def testUseLiveSitesFlagUnset(self):
    run_state = shared_state.SharedState(None, self.options, None)
    self.assertEqual(run_state.wpr_mode, wpr_modes.WPR_REPLAY)

  def testWPRRecordEnable(self):
    self.options.browser_options.wpr_mode = wpr_modes.WPR_RECORD
    run_state = shared_state.SharedState(None, self.options, None)
    self.assertEquals(run_state.wpr_mode, wpr_modes.WPR_RECORD)

