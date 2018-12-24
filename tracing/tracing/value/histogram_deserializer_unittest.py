# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from tracing.value import histogram_deserializer

class HistogramDeserializerUnittest(unittest.TestCase):
  def testDeserialize(self):
    hists = histogram_deserializer.Deserialize({
    })
    self.assertEqual(1, len(hists))
