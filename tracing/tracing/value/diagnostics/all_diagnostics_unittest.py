# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from tracing.value.diagnostics import all_diagnostics


class AllDiagnosticsUnittest(unittest.TestCase):

  def testGetDiagnosticClassForName(self):
    cls = all_diagnostics.GetDiagnosticClassForName('GenericSet')
    gs = cls(['foo'])
    gs_dict = gs.AsDict()
    self.assertEqual(gs_dict['type'], 'GenericSet')
