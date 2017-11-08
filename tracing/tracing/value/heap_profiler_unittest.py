# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from tracing.value import heap_profiler
from tracing.value import histogram
from tracing.value import histogram_set


class HeapProfilerUnitTest(unittest.TestCase):

  def testHeapProfiler(self):
    test_data = histogram_set.HistogramSet()
    for i in xrange(10):
      test_hist = histogram.Histogram('test', 'n%')
      test_hist.AddSample(i / 10.0)
      test_data.AddHistogram(test_hist)

    results = heap_profiler.HeapProfiler().Profile(test_data)

    set_size_hist = results.GetHistogramNamed('heap:HistogramSet')
    self.assertEquals(set_size_hist.num_values, 1)
    self.assertEquals(set_size_hist.sum, 32627)

    hist_size_hist = results.GetHistogramNamed('heap:Histogram')
    self.assertEquals(hist_size_hist.num_values, 10)
    self.assertEquals(hist_size_hist.sum, 29825)

    bin_size_hist = results.GetHistogramNamed('heap:HistogramBin')
    self.assertEquals(bin_size_hist.num_values, 32)
    self.assertEquals(bin_size_hist.sum, 6696)

    diag_map_size_hist = results.GetHistogramNamed('heap:DiagnosticMap')
    self.assertEquals(diag_map_size_hist.num_values, 10)
    self.assertEquals(diag_map_size_hist.sum, 2824)

    range_size_hist = results.GetHistogramNamed('heap:Range')
    self.assertEquals(range_size_hist.num_values, 22)
    self.assertEquals(range_size_hist.sum, 2088)

    stats_size_hist = results.GetHistogramNamed('heap:RunningStatistics')
    self.assertEquals(stats_size_hist.num_values, 10)
    self.assertEquals(stats_size_hist.sum, 1784)
