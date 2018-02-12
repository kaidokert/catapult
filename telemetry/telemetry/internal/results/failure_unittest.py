# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from telemetry.internal.results import failure


class ValueTest(unittest.TestCase):
  def testRepr(self):
    f = failure.Failure.FromMessage('Failure', False)

    exc_info_str = failure.GetStringFromExcInfo(f.exc_info)
    expected = 'Failure(%s, False)' % exc_info_str

    self.assertEquals(expected, str(f))
