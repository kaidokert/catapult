# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import unittest

from tracing.value import histogram_unittest
from tracing.value.diagnostics import related_event_set
from tracing.value.diagnostics import diagnostic


class RelatedEventSetUnittest(unittest.TestCase):
  def testRoundtrip(self):
    events = related_event_set.RelatedEventSet()
    events.Add({
        'stableId': '0.0',
        'title': 'foo',
        'start': 0,
        'duration': 1,
    })
    d = events.AsDict(None)
    clone = diagnostic.FromDict('RelatedEventSet', d, object())
    self.assertEqual(
        histogram_unittest.ToJSON(d),
        histogram_unittest.ToJSON(clone.AsDict(None)))
    self.assertEqual(len(events), 1)
    event = list(events)[0]
    self.assertEqual(event['stableId'], '0.0')
    self.assertEqual(event['title'], 'foo')
    self.assertEqual(event['start'], 0)
    self.assertEqual(event['duration'], 1)
