# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections
import contextlib
import gzip
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time


try:
  StringTypes = basestring
except NameError:
  StringTypes = str


_TRACING_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            os.path.pardir, os.path.pardir)
_TRACE2HTML_PATH = os.path.join(_TRACING_DIR, 'bin', 'trace2html')


class NonSerializableTraceData(Exception):
  """Raised when raw trace data cannot be serialized."""
  pass


class TraceDataPart(object):
  """Trace data can come from a variety of tracing agents.

  Data from each agent is collected into a trace "part" and accessed by the
  following fixed field names.
  """
  def __init__(self, raw_field_name):
    self._raw_field_name = raw_field_name

  def __repr__(self):
    return 'TraceDataPart("%s")' % self._raw_field_name

  @property
  def raw_field_name(self):
    return self._raw_field_name

  def __eq__(self, other):
    return self.raw_field_name == other.raw_field_name

  def __hash__(self):
    return hash(self.raw_field_name)


ANDROID_PROCESS_DATA_PART = TraceDataPart('androidProcessDump')
ATRACE_PART = TraceDataPart('systemTraceEvents')
ATRACE_PROCESS_DUMP_PART = TraceDataPart('atraceProcessDump')
CHROME_TRACE_PART = TraceDataPart('traceEvents')
CPU_TRACE_DATA = TraceDataPart('cpuSnapshots')
TELEMETRY_PART = TraceDataPart('telemetry')
WALT_TRACE_PART = TraceDataPart('waltTraceEvents')

ALL_TRACE_PARTS = {ANDROID_PROCESS_DATA_PART,
                   ATRACE_PART,
                   ATRACE_PROCESS_DUMP_PART,
                   CHROME_TRACE_PART,
                   CPU_TRACE_DATA,
                   TELEMETRY_PART}

ALL_TRACE_PARTS_RAW_NAMES = set(k.raw_field_name for k in ALL_TRACE_PARTS)


class RawTraceData(object):
  """Provides in-memory access to traces collected from tracing agents.

  Instances are created by calling the AsRawData() method on a TraceDataBuilder.

  Note: this API allows direct access to trace data in memory and, thus,
  may require a lot of memory if the traces to process are very large.
  This has lead to OOM errors in Telemetry in the past (e.g. crbug/672097).

  TODO(crbug/928278): This object is provided only to support legacy TBMv1
  metric computation, and should be removed when no such clients remain. New
  clients should instead call SerializeAsHtml() on the TraceDataWriter and
  pass the serialized output to an external trace processing script.
  """
  def __init__(self, raw_data):
    self._raw_data = raw_data

  @classmethod
  def FromChromeEvents(cls, events):
    assert isinstance(events, list)
    return cls({CHROME_TRACE_PART.raw_field_name: {'traceEvents': events}})

  @property
  def active_parts(self):
    return {p for p in ALL_TRACE_PARTS if p.raw_field_name in self._raw_data}

  def GetTracesFor(self, part):
    """Return the list of traces for |part| in string or dictionary forms."""
    return self._raw_data.get(part.raw_field_name, [])

  def GetTraceFor(self, part):
    traces = self.GetTracesFor(part)
    assert len(traces) == 1
    return traces[0]


_TraceHandle = collections.namedtuple(
    '_TraceHandle', ['part_name', 'handle', 'compressed'])


class TraceDataBuilder(object):
  """TraceDataBuilder helps build up a trace from multiple trace agents."""
  def __init__(self):
    self._temp_dir = tempfile.mkdtemp()
    self._traces = []
    self._frozen = False
    self._discard_mode = False

  def __enter__(self):
    return self

  def __exit__(self, *args):
    self.CleanUpTraceData()

  @contextlib.contextmanager
  def CollectionMode(self, discard):
    previous_mode = self._discard_mode
    try:
      self._discard_mode = bool(discard)
      yield
    finally:
      self._discard_mode = previous_mode

  def OpenTraceHandleFor(self, part, compressed=False):
    assert not self._frozen, 'Trace builder is frozen, cannot write more data'
    assert isinstance(part, TraceDataPart), part
    if self._discard_mode:
      return open(os.devnull, 'w')
    trace = _TraceHandle(
        part_name=part.raw_field_name,
        handle=tempfile.NamedTemporaryFile(delete=False, dir=self._temp_dir),
        compressed=compressed)
    self._traces.append(trace)
    return trace.handle

  def AddTraceFor(self, part, trace, binary=False):
    if isinstance(trace, StringTypes):
      assert binary
      do_write = lambda f: f.write(trace)
    elif isinstance(trace, (dict, list)):
      assert not binary
      do_write = lambda f: json.dump(trace, f)
    else:
      raise TypeError('Invalid trace data type')

    with self.OpenTraceHandleFor(part) as th:
      do_write(th)

  def Freeze(self):
    if self._frozen:
      return  # Already frozen.
    # Make sure all handles were closed, so no more writting is allowed.
    # Note it's fine if we close them multiple times.
    for trace in self._traces:
      trace.handle.close()
    self._frozen = True

  def CleanUpTraceData(self):
    if self._traces is None:
      return  # Already cleaned up.
    self.Freeze()  # Ensure all trace handles are closed.
    shutil.rmtree(self._temp_dir)
    self._temp_dir = None
    self._traces = None

  def Serialize(self, file_path, trace_title=None, clean_up=False):
    """Serializes the trace result to |file_path| and cleans up trace data."""
    try:
      self.Freeze()
      if not self._traces:
        # TODO: Should this be an error?
        logging.warning('No traces to serialize.')
        return

      cmd = ['python', _TRACE2HTML_PATH]
      trace_size = 0
      for trace in self._traces:
        trace_size += os.path.getsize(trace.handle.name)
        cmd.append(trace.handle.name)
      logging.info('Collected %d traces with a total of %d bytes',
                   len(self._traces), trace_size)
      cmd.extend(['--output', file_path])
      if trace_title is not None:
        cmd.extend(['--title', trace_title])

      start_time = time.time()
      subprocess.check_output(cmd)
      elapsed_time = time.time() - start_time
      logging.info('trace2html finished in %.02f seconds.', elapsed_time)
    finally:
      if clean_up:
        self.CleanUpTraceData()

  def AsRawTraceData(self, clean_up=False):
    """Allow in-memory access to read the collected trace data.

    WARNING: this can have large memory footprint if the trace data is big.

    This method is only provided as a convenience for some tests that need
    to verify whether trace data is being properly written by tracing agents,
    and to support some legacy TBMv1 clients (http://crbug/928278). It should
    not be used in any other context; Telemetry aims to remain a strict trace
    data writer (no reading).
    """
    try:
      self.Freeze()
      assert self._traces is not None, 'Trace data has been already cleaned up'
      assert all(t.handle.closed for t in self._traces), (
          'Some trace handles have not been properly closed')

      raw_data = {}
      for trace in self._traces:
        part_traces = raw_data.setdefault(trace.name_part, [])
        opener = gzip.open if trace.compressed else open
        with opener(trace.handle.name, 'rb') as f:
          part_traces.append(json.load(f))

      return RawTraceData(raw_data)
    finally:
      if clean_up:
        self.CleanUpTraceData()
