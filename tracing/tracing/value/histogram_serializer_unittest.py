# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from tracing.value import histogram
from tracing.value import histogram_serializer
from tracing.value.diagnostics import breakdown
from tracing.value.diagnostics import generic_set
from tracing.value.diagnostics import related_event_set
from tracing.value.diagnostics import related_name_map


class HistogramSerializerUnittest(unittest.TestCase):
  def testSerialize(self):
    hist = histogram.Histogram('aaa', 'count_biggerIsBetter')
    hist.diagnostics['bbb'] = related_name_map.RelatedNameMap({
        'ccc': 'a:c',
        'ddd': 'a:d',
    })
    hist.diagnostics['hhh'] = generic_set.GenericSet(['ggg'])
    hist.AddSample(0, {
        'bbb': breakdown.Breakdown.FromEntries({
            'ccc': 11,
            'ddd': 31,
        }),
        'eee': related_event_set.RelatedEventSet([{
            'stableId': 'fff',
            'title': 'ggg',
            'start': 3,
            'duration': 4,
        }]),
    })

    self.assertEqual(histogram_serializer.Serialize([hist]), [
        [
            "aaa",
            [1, [1, 1000.0, 20]],
            "",
            "ccc",
            "ddd",
            [3, 4],
            "ggg",
            "a:c",
            "a:d",
        ],
        {
            "RelatedNameMap": {"bbb": {1: [5, 7, 8]}},
            "GenericSet": {"hhh": {0: 6}},
            "Breakdown": {"bbb": {3: [2, 5, 11, 31]}},
            "RelatedEventSet": {"eee": {2: [["fff", 6, 3, 4]]}}
        },
        [
            0,
            "count+",
            1,
            2,
            [0, 1],
            [1, 0, None, 0, 0, 0, 0],
            {0: [1, [None, 2, 3]]},
            0
        ]
    ])
