# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import gc
import sys
import traceback
import uuid

from py_trace_event import trace_event
from telemetry.core import exceptions
from telemetry.internal.platform.tracing_agent import atrace_tracing_agent
from telemetry.internal.platform.tracing_agent import chrome_tracing_agent
from telemetry.internal.platform.tracing_agent import cpu_tracing_agent
from telemetry.internal.platform.tracing_agent import display_tracing_agent
from telemetry.internal.platform.tracing_agent import telemetry_tracing_agent
from telemetry.timeline import tracing_config
from tracing.trace_data import trace_data


_TRACING_AGENT_CLASSES = (
    telemetry_tracing_agent,
    chrome_tracing_agent,
    atrace_tracing_agent,
    cpu_tracing_agent,
    display_tracing_agent
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
    self._supported_agents_classes = [
        agent_classes for agent_classes in _TRACING_AGENT_CLASSES if
        agent_classes.IsSupported(platform_backend)]
    self._active_agents_instances = []
    self._trace_log = None
    self._nonfatal_exceptions = []

  # TODO(charliea): Remove all logic supporting the notion of nonfatal
  # exceptions. BattOr was the only use case for this logic, and we no longer
  # support BattOr tracing in Telemetry.
  @contextlib.contextmanager
  def _CollectNonfatalException(self, context_description):
    """Collects any nonfatal exceptions that occur in the context, adding them
    to self._nonfatal_exceptions and logging them.

    Args:
      context_description: A string description of the context to be used in
          logging.
    """
    del context_description
    yield

  def StartTracing(self, config, timeout):
    if self.is_tracing_running:
      return False

    assert isinstance(config, tracing_config.TracingConfig)
    assert len(self._active_agents_instances) == 0

    self._current_state = _TracingState(config, timeout)
    # Hack: chrome tracing agent may only depend on the number of alive chrome
    # devtools processes, rather platform (when startup tracing is not
    # supported), hence we add it to the list of supported agents here if it was
    # not added.
    if (chrome_tracing_agent.ChromeTracingAgent.IsSupported(
        self._platform_backend) and
        not chrome_tracing_agent.ChromeTracingAgent in
        self._supported_agents_classes):
      self._supported_agents_classes.append(
          chrome_tracing_agent.ChromeTracingAgent)

    self.StartAgentTracing(config, timeout)
    for agent_class in self._supported_agents_classes:
      agent = agent_class(self._platform_backend)
      with trace_event.trace('StartAgentTracing',
                             agent=str(agent.__class__.__name__)):
        with self._CollectNonfatalException('StartAgentTracing'):
          if agent.StartAgentTracing(config, timeout):
            self._active_agents_instances.append(agent)

    return True

  def StopTracing(self):
    assert self.is_tracing_running, 'Can only stop tracing when tracing is on.'
    self._IssueClockSyncMarker()
    builder = self._current_state.builder

    raised_exception_messages = []
    for agent in self._active_agents_instances:
      try:
        with trace_event.trace('StopAgentTracing',
                               agent=str(agent.__class__.__name__)):
          with self._CollectNonfatalException('StopAgentTracing'):
            agent.StopAgentTracing()
      except Exception: # pylint: disable=broad-except
        raised_exception_messages.append(
            ''.join(traceback.format_exception(*sys.exc_info())))

    for agent in self._active_agents_instances + [self]:
      try:
        with trace_event.trace('CollectAgentTraceData',
                               agent=str(agent.__class__.__name__)):
          with self._CollectNonfatalException('CollectAgentTraceData'):
            agent.CollectAgentTraceData(builder)
      except Exception: # pylint: disable=broad-except
        raised_exception_messages.append(
            ''.join(traceback.format_exception(*sys.exc_info())))

    self._active_agents_instances = []
    self._current_state = None

    if raised_exception_messages:
      raise exceptions.TracingException(
          'Exceptions raised when trying to stop tracing:\n' +
          '\n'.join(raised_exception_messages))

    return (builder.AsData(), self._nonfatal_exceptions)

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
            with self._CollectNonfatalException('FlushAgentTracing'):
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

  def _IssueClockSyncMarker(self):
    with _DisableGarbageCollection():
      for agent in self._active_agents_instances:
        if agent.SupportsExplicitClockSync():
          sync_id = _GenerateClockSyncId()
          with trace_event.trace('RecordClockSyncMarker',
                                 agent=str(agent.__class__.__name__),
                                 sync_id=sync_id):
            with self._CollectNonfatalException('RecordClockSyncMarker'):
              agent.RecordClockSyncMarker(
                  sync_id, telemetry_tracing_agent.RecordClockSyncCallback)

  def IsChromeTracingSupported(self):
    return chrome_tracing_agent.ChromeTracingAgent.IsSupported(
        self._platform_backend)

  @property
  def is_tracing_running(self):
    return self._current_state is not None

  @property
  def is_chrome_tracing_running(self):
    return self.is_tracing_running and any(
        isinstance(agent, chrome_tracing_agent.ChromeTracingAgent)
        for agent in self._active_agents_instances)

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
