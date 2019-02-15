# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import ast
import logging
import tempfile
import os

from telemetry.internal.platform import tracing_agent
from tracing.trace_data import trace_data

from py_trace_event import trace_event
from py_utils import atexit_with_log


class TelemetryTracingAgent(tracing_agent.TracingAgent):
  """TODO"""

  def __init__(self, platform_backend):
    super(TelemetryTracingAgent, self).__init__(platform_backend)
    self._trace_log = None
    self._telemetry_info = None

  @classmethod
  def IsSupported(cls, platform_backend):
    del platform_backend  # unused
    return trace_event.is_tracing_controllable()

  @property
  def is_tracing(self):
    return trace_event.trace_is_enabled()

  def SetTelemetryInfo(self, telemetry_info):
    self._telemetry_info = telemetry_info

  def StartAgentTracing(self, config, timeout):
    del config  # Unused.
    del timeout  # Unused.
    assert not self.is_tracing, 'Telemetry tracing already running'
    with tempfile.NamedTemporaryFile(delete=False) as tf:
      self._trace_log = tf.name
    trace_event.trace_enable(self._trace_log)
    assert self.is_tracing, 'Failed to start Telemetry tracing'
    return True

  def StopAgentTracing(self):
    assert self.is_tracing, 'Telemetry tracing is not running'
    trace_event.trace_disable()
    assert not self.is_tracing, 'Failed to stop Telemetry tracing'

  def CollectAgentTraceData(self, trace_data_builder, timeout=None):
    assert not self.is_tracing, 'Must stop tracing before collection'
    with open(self._trace_log, 'r') as f:
      data = ast.literal_eval(f.read() + ']')

    trace_data_builder.AddTraceFor(
        trace_data.TELEMETRY_PART,
        {
            "traceEvents": data,
            "metadata": {
                # TODO(charliea): For right now, we use "TELEMETRY" as the clock
                # domain to guarantee that Telemetry is given its own clock
                # domain. Telemetry isn't really a clock domain, though: it's a
                # system that USES a clock domain like LINUX_CLOCK_MONOTONIC or
                # WIN_QPC. However, there's a chance that a Telemetry controller
                # running on Linux (using LINUX_CLOCK_MONOTONIC) is interacting
                # with an Android phone (also using LINUX_CLOCK_MONOTONIC, but
                # on a different machine). The current logic collapses clock
                # domains based solely on the clock domain string, but we really
                # should to collapse based on some (device ID, clock domain ID)
                # tuple. Giving Telemetry its own clock domain is a work-around
                # for this.
                "clock-domain":
                    "TELEMETRY",
                "telemetry": (self._telemetry_info.AsDict()
                              if self._telemetry_info else {}),
            }
        })
    try:
      os.remove(self._trace_log)
    except OSError:
      logging.error('Error when deleting %s, will try again at exit.',
                    self._trace_log)
      def DeleteAtExit(path):
        os.remove(path)
      atexit_with_log.Register(DeleteAtExit, self._trace_log)
    finally:
      self._trace_log = None

  @staticmethod
  def RecordIssuerClockSyncMarker(sync_id, issue_ts):
    """ Record clock sync event.

    Args:
      sync_id: Unqiue id for sync event.
      issue_ts: timestamp before issuing clocksync to agent.
    """
    trace_event.clock_sync(sync_id, issue_ts=issue_ts)
