# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from telemetry.util import heap_metric

from tracing.value import histogram
from tracing.value import histogram_set


class HeapMetricUnitTest(unittest.TestCase):

  def testHeapMetric(self):
    test_data = histogram_set.HistogramSet()
    for i in xrange(10):
      test_hist = histogram.Histogram('test', 'n%')
      test_hist.AddSample(i / 10.0)
      test_data.AddHistogram(test_hist)

    results = heap_metric.HeapMetric(test_data)

    set_size_hist = results.GetHistogramNamed('HistogramSet')
    self.assertEquals(set_size_hist.num_values, 1)
    self.assertEquals(set_size_hist.sum, 2522)

    hist_size_hist = results.GetHistogramNamed('Histogram')
    self.assertEquals(hist_size_hist.num_values, 10)
    self.assertEquals(hist_size_hist.sum, 28275)

    bin_size_hist = results.GetHistogramNamed('HistogramBin')
    self.assertEquals(bin_size_hist.num_values, 220)
    self.assertEquals(bin_size_hist.sum, 91683)

    diag_map_size_hist = results.GetHistogramNamed('DiagnosticMap')
    self.assertEquals(diag_map_size_hist.num_values, 10)
    self.assertEquals(diag_map_size_hist.sum, 2800)

    range_size_hist = results.GetHistogramNamed('Range')
    self.assertEquals(range_size_hist.num_values, 22)
    self.assertEquals(range_size_hist.sum, 8269)

    stats_size_hist = results.GetHistogramNamed('RunningStatistics')
    self.assertEquals(stats_size_hist.num_values, 10)
    self.assertEquals(stats_size_hist.sum, 12015)
