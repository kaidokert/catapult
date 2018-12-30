# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from tracing.value import histogram
from tracing.value import histogram_deserializer
from tracing.value.diagnostics import breakdown
from tracing.value.diagnostics import date_range
from tracing.value.diagnostics import generic_set
from tracing.value.diagnostics import related_event_set
from tracing.value.diagnostics import related_name_map

class HistogramDeserializerUnittest(unittest.TestCase):
  def testDeserialize(self):
    hists = histogram_deserializer.Deserialize({
        'n': ['aaa', 'bbb', 'ccc'],
        'd': {
            'GenericSet': {
                'ddd': {
                    0: ['eee'],
                },
            },
            'DateRange': {
                'fff': {
                    1: 1545682260742,
                },
            },
            'Breakdown': {
                'ggg': {
                    2: ['colorscheme', {
                        'hhh': 4,
                        'iii': 6,
                    }],
                },
            },
            'RelatedNameMap': {
                'jjj': {
                    3: {
                        'lll': 1,
                        'mmm': 2,
                    },
                },
            },
            'RelatedEventSet': {
                'nnn': {
                    4: [
                        {
                            'stableId': 'a.0.b.1.c.2',
                            'title': 'Title',
                            'start': 0,
                            'duration': 1,
                        },
                    ],
                },
            },
        },
        'h': [
            {
                'B': {1: [1, [[2, 4]]]},
                'b': [0, [0, 100, 10]],
                'd': 'description',
                'D': [0, 1, 3],
                'g': 'guid',
                'm': 100,
                'n': 0,
                'a': [2, [[0, 4]]],
                'r': [1, 1, 1, 1, 1, 1, 1],
                'v': [42],
                'o': {'nans': True},
                'u': 'ms',
            },
        ],
    })
    self.assertEqual(1, len(hists))
    hist = list(hists)[0]
    self.assertIsInstance(hist, histogram.Histogram)
    self.assertEqual('aaa', hist.name)
    self.assertEqual('ms', hist.unit)
    self.assertEqual('guid', hist.guid)
    self.assertEqual(1, hist.average)
    self.assertEqual(1, hist.num_values)
    self.assertEqual(0, hist.standard_deviation)
    self.assertEqual(1, hist.sum)
    self.assertEqual(1, hist.running.min)
    self.assertEqual(1, hist.running.max)

    fff = hist.diagnostics.get('fff')
    self.assertIsInstance(fff, date_range.DateRange)
    self.assertEqual(1545682260742, fff.min_timestamp)
    self.assertEqual(1545682260742, fff.max_timestamp)

    jjj = hist.diagnostics.get('jjj')
    self.assertIsInstance(jjj, related_name_map.RelatedNameMap)
    self.assertEqual(jjj.Get('lll'), 'bbb')
    self.assertEqual(jjj.Get('mmm'), 'ccc')

    ddd = hist.diagnostics.get('ddd')
    self.assertIsInstance(ddd, generic_set.GenericSet)
    self.assertEqual('eee', list(ddd)[0])

    self.assertEqual(2, hist.num_nans)
    self.assertEqual(len(hist.nan_diagnostic_maps), 1)
    ddd = hist.nan_diagnostic_maps[0].get('ddd')
    self.assertIsInstance(ddd, generic_set.GenericSet)
    self.assertEqual('eee', list(ddd)[0])
    nnn = hist.nan_diagnostic_maps[0].get('nnn')
    self.assertIsInstance(nnn, related_event_set.RelatedEventSet)
    self.assertEqual(len(nnn), 1)

    self.assertEqual(len(hist.bins), 12)
    b = hist.bins[1]
    self.assertEqual(len(b.diagnostic_maps), 1)
    dm = b.diagnostic_maps[0]
    self.assertEqual(len(dm), 2)
    ggg = dm.get('ggg')
    self.assertIsInstance(ggg, breakdown.Breakdown)
    self.assertEqual('colorscheme', ggg.color_scheme)
    self.assertEqual(len(ggg), 2)
    self.assertEqual(4, ggg.Get('hhh'))
    self.assertEqual(6, ggg.Get('iii'))
