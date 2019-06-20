# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from tracing_build import snapdragon2trace


def _SDSample(value, timestamp):
  return {
      'Process': 'Global',
      'Metric': 'GPU % Utilization',
      'Value': value,
      'TimestampRaw': timestamp}


class Snapdragon2traceTests(unittest.TestCase):

  def testAddSnapdragonProfilerData(self):
    snapdragon_csv = [_SDSample(i + 1, 1000 + i * 100) for i in range(10)]
    traces = [{
        'traceEvents': [
            {'pid': 1, 'tid': 1, 'ph': 'X', 'dur': 10, 'ts': 350},
            {'pid': 1, 'tid': 1, 'ph': 'X', 'dur': 10, 'ts': 450},
            {'pid': 1, 'tid': 1, 'ph': 'X', 'dur': 10, 'ts': 550},
            {'pid': 2, 'tid': 2, 'ph': 'X', 'dur': 10, 'ts': 400},
            {'pid': 2, 'tid': 2, 'ph': 'X', 'dur': 100, 'ts': 650},
            {'pid': 3, 'tid': 3, 'ph': 'X', 'dur': 10, 'ts': 500},
            {'pid': 3, 'tid': 3, 'ph': 'X', 'dur': 10, 'ts': 550}],
        'metadata': {'clock-offset-since-epoch': '1000'}}]
    snapdragon2trace.AddSnapdragonProfilerData(traces, snapdragon_csv)
    print 'traces: %s' % str(traces)
