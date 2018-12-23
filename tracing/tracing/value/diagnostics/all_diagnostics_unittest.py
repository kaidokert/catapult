# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from tracing.value.diagnostics import all_diagnostics


class AllDiagnosticsUnittest(unittest.TestCase):

  def testGetDiagnosticClassForName_Bogus(self):
    self.assertRaises(
        AssertionError, all_diagnostics.GetDiagnosticClassForName, 'BogusDiag')
