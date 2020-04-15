# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import logging
import time

from telemetry.core import exceptions
from telemetry.internal.platform import tracing_agent

from devil.android import device_temp_file
from tracing.trace_data import trace_data


ANDROID_TRACES_DIR = '/data/misc/perfetto-traces'
ANDROID_TRACED = 'traced'
ANDROID_TRACED_PROBES = 'traced_probes'
ANDROID_PERFETTO = 'perfetto'
ANDROID_TRIGGER_PERFETTO = 'trigger_perfetto'
_ALL_ANDROID_BINS = (
    ANDROID_TRACED,
    ANDROID_TRACED_PROBES,
    ANDROID_PERFETTO,
    ANDROID_TRIGGER_PERFETTO)

_IN_BACKGROUND = ' </dev/null >/dev/null 2>&1 &'
_TRACE_CONFIG = """
buffers: {{
    size_kb: 200000
    fill_policy: DISCARD
}}
data_sources: {{
    config {{
        name: "org.chromium.trace_event"
        chrome_config {{
            trace_config: {chrome_trace_config}
        }}
    }}
}}
data_sources: {{
    config {{
        name: "org.chromium.trace_metadata"
        chrome_config {{
            trace_config: {chrome_trace_config}
        }}
    }}
}}
trigger_config: {{
  trigger_mode: STOP_TRACING
  triggers: {{
    name: "stop_telemetry_system_tracing"
    stop_delay_ms: 0
  }}
  trigger_timeout_ms: {trigger_timeout_ms}
}}
"""


class PerfettoTracingAgent(tracing_agent.TracingAgent):
  def __init__(self, platform_backend):
    super(PerfettoTracingAgent, self).__init__(platform_backend)
    self._device = platform_backend.device
    self._finish_stamp_temp_file = None
    self._trace_config_temp_file = None
    self._trace_output_temp_file = None

  @classmethod
  def SetUpAgent(cls, platform_backend):
    """Install and start required traced binaries."""
    if not cls.IsSupported(platform_backend):
      return
    device = platform_backend.device
    processes = set(p.name for p in device.ListProcesses())
    assert ANDROID_TRACED in processes
    assert ANDROID_TRACED_PROBES in processes
    with device.adb.PersistentShell(device.adb.GetDeviceSerial()) as pshell:
      pshell.RunCommand('mkdir ' + ANDROID_TRACES_DIR)
    logging.warning('Perfetto tracing agent is set up.')

  @classmethod
  def IsSupported(cls, platform_backend):
    return platform_backend.GetOSName() == 'android'

  def _PersistentShell(self):
    serial = self._device.adb.GetDeviceSerial()
    return self._device.adb.PersistentShell(serial)

  def _TempFile(self, **kwargs):
    return device_temp_file.DeviceTempFile(
        self._device.adb, dir=ANDROID_TRACES_DIR, **kwargs)

  def StartAgentTracing(self, config, timeout):
    del timeout  # Unused.
    self._finish_stamp_temp_file = self._TempFile(suffix='.stamp')
    self._trace_config_temp_file = self._TempFile(suffix='.txt')
    self._trace_output_temp_file = self._TempFile(suffix='.pb')
    self._device.WriteFile(
        self._trace_config_temp_file.name, ConfigToTextProto(config))
    start_perfetto = 'sh -c "%s --config %s --txt --out %s && touch %s"' % (
        ANDROID_PERFETTO,
        self._trace_config_temp_file.name,
        self._trace_output_temp_file.name,
        self._finish_stamp_temp_file.name,
    )
    with self._PersistentShell() as pshell:
      pshell.RunCommand(start_perfetto + _IN_BACKGROUND, close=True)
    logging.warning('Started perfetto system tracing.')
    return True

  def StopAgentTracing(self):
    self._device.RunShellCommand(
        [ANDROID_TRIGGER_PERFETTO, 'stop_telemetry_system_tracing'],
        check_return=True)
    logging.warning('Stopped perfetto system tracing.')

  def CollectAgentTraceData(self, trace_data_builder, timeout=60):
    start_time = time.time()
    with trace_data_builder.OpenTraceHandleFor(
        trace_data.CHROME_TRACE_PART, suffix='.pb') as handle:
      pass
    while not self._device.PathExists([self._finish_stamp_temp_file.name]):
      time.sleep(.1)
      if time.time() - start_time >= timeout:
        raise exceptions.TimeoutException()
    timeout -= time.time() - start_time
    self._device.PullFile(
        self._trace_output_temp_file.name, handle.name, timeout=timeout)
    self._finish_stamp_temp_file.close()
    self._trace_config_temp_file.close()
    self._trace_output_temp_file.close()
    self._finish_stamp_temp_file = None
    self._trace_config_temp_file = None
    self._trace_output_temp_file = None
    logging.warning('Collected trace from perfetto system tracing.')


def ConfigToTextProto(config):
  # TODO: Relax this assert.
  assert config.enable_chrome_trace, 'Chrome tracing must be enabled'
  chrome_trace_config = (
      config.chrome_trace_config.GetChromeTraceConfigForStartupTracing())
  # Note: The inner json.dumps is to serialize the chrome_trace_config dict
  # into a json string. The second outer json.dumps is to convert that to
  # a string literal to paste into the text proto config.
  chrome_trace_config = json.dumps(
      json.dumps(chrome_trace_config, sort_keys=True, separators=(',', ':')))
  trace_config = _TRACE_CONFIG.format(
      chrome_trace_config=chrome_trace_config,
      trigger_timeout_ms=30*60*1000  # Half an hour.
  )
  return trace_config
