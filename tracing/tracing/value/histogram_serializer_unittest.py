# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from tracing.value import histogram_serializer
from tracing.value.diagnostics import generic_set


class HistogramSerializerUnittest(unittest.TestCase):
  def testObjects(self):
    serializer = histogram_serializer.HistogramSerializer()
    self.assertEqual(0, serializer.GetId('a'))
    self.assertEqual(1, serializer.GetId(['b']))
    self.assertEqual(0, serializer.GetId('a'))
    self.assertEqual(1, serializer.GetId(['b']))

  def testDiagnostics(self):
    serializer = histogram_serializer.HistogramSerializer()
    self.assertEqual(0, serializer.GetDiagnosticId(
        'a', generic_set.GenericSet(['b'])))
    self.assertEqual(1, serializer.GetDiagnosticId(
        'a', generic_set.GenericSet(['c'])))
    self.assertEqual(0, serializer.GetDiagnosticId(
        'a', generic_set.GenericSet(['b'])))
    self.assertEqual(1, serializer.GetDiagnosticId(
        'a', generic_set.GenericSet(['c'])))
