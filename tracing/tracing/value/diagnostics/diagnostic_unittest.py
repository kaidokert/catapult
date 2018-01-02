# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

#TODO(#3613): Remove this import.
from tracing.value import histogram  # pylint:disable=unused-import
from tracing.value.diagnostics import all_diagnostics


class DiagnosticUnittest(unittest.TestCase):

  def testEqualityForSmoke(self):
    self.assertGreater(len(all_diagnostics.DIAGNOSTICS_BY_NAME), 0)
    for ctor in all_diagnostics.DIAGNOSTICS_BY_NAME.itervalues():
      self.assertTrue(hasattr(ctor, '__eq__'))
