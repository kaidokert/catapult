# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest

from tracing.trace_data import trace_data
from tracing_build import html2trace
from py_utils import tempfile_ext


class TraceDataTest(unittest.TestCase):
  def testListForm(self):
    d = trace_data.RawTraceData.FromChromeEvents([{'ph': 'B'}])
    events = d.GetTraceFor(trace_data.CHROME_TRACE_PART)['traceEvents']
    self.assertEquals(1, len(events))


class TraceDataBuilderTest(unittest.TestCase):
  def testSerialize(self):
    trace = {'traceEvents': [1, 2, 3]}
    with tempfile_ext.NamedTemporaryDirectory() as test_dir:
      trace_path = os.path.join(test_dir, 'test_trace.json')
      with trace_data.TraceDataBuilder() as builder:
        builder.AddTraceFor(trace_data.CHROME_TRACE_PART, trace)
        builder.Serialize(trace_path)
      with open(trace_path) as f:
        got_traces = html2trace.ReadTracesFromHTMLFile(f)
    self.assertEqual(got_traces, [trace])

  def testAsRawTraceData(self):
    trace = {'traceEvents': [1, 2, 3]}
    with trace_data.TraceDataBuilder() as builder:
      builder.AddTraceFor(trace_data.CHROME_TRACE_PART, trace)
      raw_data = builder.AsRawTraceData()
    got_traces = raw_data.GetTracesFor(trace_data.CHROME_TRACE_PART)
    self.assertEqual(got_traces, [trace])
