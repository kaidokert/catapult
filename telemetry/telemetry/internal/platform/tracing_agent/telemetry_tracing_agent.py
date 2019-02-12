# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import tempfile

from py_trace_event import trace_event


class TelemetryTracingAgent(object): # tracing_agent.TracingAgent):
  def __init__(self, platform_backend):
    super(TelemetryTracingAgent, self).__init__(platform_backend)
    self._trace_log = None

  @classmethod
  def IsSupported(cls, platform_backend):
    del platform_backend  # Unused.
    return trace_event.is_tracing_controllable()

  def StartAgentTracing(self, config, timeout):
    assert not trace_event.trace_is_enabled(), (
        'Telemetry tracing already started')
    del config # Unused.
    del timeout # Unused.

    with tempfile.NamedTemporaryFile(delete=False) as tf:
      self._trace_log = tf.name

    trace_event.trace_enable(self._trace_log)
    assert trace_event.trace_is_enabled(), 'Could not start Telemetry tracing'
    return True

  def StopAgentTracing(self):
    raise NotImplementedError

  def SupportsExplicitClockSync(self):
    return True

  def RecordClockSyncMarker(self, sync_id,
                            record_controller_clock_sync_marker_callback):
    raise NotImplementedError

  def CollectAgentTraceData(self, trace_data_builder, timeout=None):
    raise NotImplementedError
