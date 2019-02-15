# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import ast
import contextlib
import gc
import logging
import os
import sys
import tempfile
import traceback
import uuid

from py_trace_event import trace_event
from telemetry.core import exceptions
from telemetry.internal.platform.tracing_agent import atrace_tracing_agent
from telemetry.internal.platform.tracing_agent import chrome_tracing_agent
from telemetry.internal.platform.tracing_agent import cpu_tracing_agent
from telemetry.internal.platform.tracing_agent import display_tracing_agent
from telemetry.timeline import tracing_config
from tracing.trace_data import trace_data

from py_utils import atexit_with_log


_TRACING_AGENT_CLASSES = (
    chrome_tracing_agent.ChromeTracingAgent,
    atrace_tracing_agent.AtraceTracingAgent,
    cpu_tracing_agent.CpuTracingAgent,
    display_tracing_agent.DisplayTracingAgent
)


def _GenerateClockSyncId():
  return str(uuid.uuid4())


@contextlib.contextmanager
def _DisableGarbageCollection():
  try:
    gc.disable()
    yield
  finally:
    gc.enable()


class _TraceDataDiscarder(object):
  """A do-nothing data builder that just discards trace data."""
  def AddTraceFor(self, trace_part, value):
    del trace_part  # Unused.
    del value  # Unused.


class _TracingState(object):

  def __init__(self, config, timeout):
    self._builder = trace_data.TraceDataBuilder()
    self._config = config
    self._timeout = timeout

  @property
  def builder(self):
    return self._builder

  @property
  def config(self):
    return self._config

  @property
  def timeout(self):
    return self._timeout


class TracingControllerBackend(object):
  def __init__(self, platform_backend):
    self._platform_backend = platform_backend
    self._current_state = None
    self._active_agents_instances = []
    self._trace_log = None
    self._is_tracing_controllable = True
    self._telemetry_info = None

  def SetTelemetryInfo(self, telemetry_info):
    self._telemetry_info = telemetry_info

  def StartTracing(self, config, timeout):
    if self.is_tracing_running:
      return False

    assert isinstance(config, tracing_config.TracingConfig)
    assert len(self._active_agents_instances) == 0

    self._current_state = _TracingState(config, timeout)

    self.StartAgentTracing(config, timeout)
    for agent_class in _TRACING_AGENT_CLASSES:
      if agent_class.IsSupported(self._platform_backend):
        agent = agent_class(self._platform_backend)
        with trace_event.trace('StartAgentTracing',
                               agent=str(agent.__class__.__name__)):
          if agent.StartAgentTracing(config, timeout):
            self._active_agents_instances.append(agent)

    return True

  def StopTracing(self):
    assert self.is_tracing_running, 'Can only stop tracing when tracing is on.'
    self._IssueClockSyncMarker()
    builder = self._current_state.builder

    raised_exception_messages = []
    for agent in self._active_agents_instances + [self]:
      try:
        with trace_event.trace('StopAgentTracing',
                               agent=str(agent.__class__.__name__)):
          agent.StopAgentTracing()
      except Exception: # pylint: disable=broad-except
        raised_exception_messages.append(
            ''.join(traceback.format_exception(*sys.exc_info())))

    for agent in self._active_agents_instances + [self]:
      try:
        with trace_event.trace('CollectAgentTraceData',
                               agent=str(agent.__class__.__name__)):
          agent.CollectAgentTraceData(builder)
      except Exception: # pylint: disable=broad-except
        raised_exception_messages.append(
            ''.join(traceback.format_exception(*sys.exc_info())))

    self._telemetry_info = None
    self._active_agents_instances = []
    self._current_state = None

    if raised_exception_messages:
      raise exceptions.TracingException(
          'Exceptions raised when trying to stop tracing:\n' +
          '\n'.join(raised_exception_messages))

    return builder.AsData()

  def FlushTracing(self, discard_current=False):
    assert self.is_tracing_running, 'Can only flush tracing when tracing is on.'
    self._IssueClockSyncMarker()

    raised_exception_messages = []

    # pylint: disable=redefined-variable-type
    # See: https://github.com/PyCQA/pylint/issues/710
    if discard_current:
      trace_builder = _TraceDataDiscarder()
    else:
      trace_builder = self._current_state.builder

    # Flushing the controller's pytrace is not supported.
    for agent in self._active_agents_instances:
      try:
        if agent.SupportsFlushingAgentTracing():
          with trace_event.trace('FlushAgentTracing',
                                 agent=str(agent.__class__.__name__)):
            agent.FlushAgentTracing(self._current_state.config,
                                    self._current_state.timeout,
                                    trace_builder)
      except Exception: # pylint: disable=broad-except
        raised_exception_messages.append(
            ''.join(traceback.format_exception(*sys.exc_info())))

    if raised_exception_messages:
      raise exceptions.TracingException(
          'Exceptions raised when trying to flush tracing:\n' +
          '\n'.join(raised_exception_messages))

  def StartAgentTracing(self, config, timeout):
    self._is_tracing_controllable = trace_event.is_tracing_controllable()
    if not self._is_tracing_controllable:
      return False

    tf = tempfile.NamedTemporaryFile(delete=False)
    self._trace_log = tf.name
    tf.close()
    del config # unused
    del timeout # unused
    assert not trace_event.trace_is_enabled(), 'Tracing already running.'
    trace_event.trace_enable(self._trace_log)
    assert trace_event.trace_is_enabled(), 'Tracing didn\'t enable properly.'
    return True

  def StopAgentTracing(self):
    if not self._is_tracing_controllable:
      return
    assert trace_event.trace_is_enabled(), 'Tracing not running'
    trace_event.trace_disable()
    assert not trace_event.trace_is_enabled(), 'Tracing didnt disable properly.'

  def SupportsExplicitClockSync(self):
    return True

  def _RecordIssuerClockSyncMarker(self, sync_id, issue_ts):
    """ Record clock sync event.

    Args:
      sync_id: Unqiue id for sync event.
      issue_ts: timestamp before issuing clocksync to agent.
    """
    if self._is_tracing_controllable:
      trace_event.clock_sync(sync_id, issue_ts=issue_ts)

  def _IssueClockSyncMarker(self):
    with _DisableGarbageCollection():
      for agent in self._active_agents_instances:
        if agent.SupportsExplicitClockSync():
          sync_id = _GenerateClockSyncId()
          with trace_event.trace('RecordClockSyncMarker',
                                 agent=str(agent.__class__.__name__),
                                 sync_id=sync_id):
            agent.RecordClockSyncMarker(sync_id,
                                        self._RecordIssuerClockSyncMarker)

  def IsChromeTracingSupported(self):
    return chrome_tracing_agent.ChromeTracingAgent.IsSupported(
        self._platform_backend)

  @property
  def is_tracing_running(self):
    return self._current_state is not None

  @property
  def is_chrome_tracing_running(self):
    return self._GetActiveChromeTracingAgent() is not None

  def _GetActiveChromeTracingAgent(self):
    if not self.is_tracing_running:
      return None
    if not self._current_state.config.enable_chrome_trace:
      return None
    for agent in self._active_agents_instances:
      if isinstance(agent, chrome_tracing_agent.ChromeTracingAgent):
        return agent
    return None

  def GetChromeTraceConfig(self):
    agent = self._GetActiveChromeTracingAgent()
    if agent:
      return agent.trace_config
    return None

  def GetChromeTraceConfigFile(self):
    agent = self._GetActiveChromeTracingAgent()
    if agent:
      return agent.trace_config_file
    return None

  def ClearStateIfNeeded(self):
    chrome_tracing_agent.ClearStarupTracingStateIfNeeded(self._platform_backend)

  def CollectAgentTraceData(self, trace_data_builder):
    if not self._is_tracing_controllable:
      return
    assert not trace_event.trace_is_enabled(), 'Stop tracing before collection.'
    with open(self._trace_log, 'r') as fp:
      data = ast.literal_eval(fp.read() + ']')
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
      self._trace_log = None
    except OSError:
      logging.exception('Error when deleting %s, will try again at exit.',
                        self._trace_log)
      def DeleteAtExit(path):
        os.remove(path)
      atexit_with_log.Register(DeleteAtExit, self._trace_log)
    self._trace_log = None
