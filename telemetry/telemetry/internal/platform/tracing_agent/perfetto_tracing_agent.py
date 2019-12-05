# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import logging
import os
import posixpath

from telemetry.internal.platform import tracing_agent

from devil.android import device_temp_file
from devil.android.sdk import version_codes
from devil.utils import cmd_helper
from tracing.trace_data import trace_data


ANDROID_BIN_DIR = '/data/local/tmp'
ANDROID_TRACES_DIR = '/data/misc/perfetto-traces'
ANDROID_TRACED = posixpath.join(ANDROID_BIN_DIR, 'traced')
ANDROID_TRACED_PROBES = posixpath.join(ANDROID_BIN_DIR, 'traced_probes')
ANDROID_PERFETTO = posixpath.join(ANDROID_BIN_DIR, 'perfetto')
ANDROID_TRIGGER_PERFETTO = posixpath.join(ANDROID_BIN_DIR, 'trigger_perfetto')
_ALL_ANDROID_BINS = (
    ANDROID_TRACED,
    ANDROID_TRACED_PROBES,
    ANDROID_PERFETTO,
    ANDROID_TRIGGER_PERFETTO)


_IN_BACKGROUND = '%s </dev/null >/dev/null 2>&1 &'
_TRACE_CONFIG = """
buffers: {{
    size_kb: 8960
    fill_policy: DISCARD
}}
buffers: {{
    size_kb: 1280
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
    self._trace_config_temp_file = None
    self._trace_output_temp_file = None

  @classmethod
  def SetUpAgent(cls, platform_backend, host_bin_dir):
    """Install and start required traced binaries."""
    if not cls.IsSupported(platform_backend):
      return
    device = platform_backend.device
    if device.build_version_sdk >= version_codes.PIE:
      return
    for device_bin in _ALL_ANDROID_BINS:
      device.KillAll(device_bin, exact=True, quiet=True)
    device.PushChangedFiles([
        (os.path.join(host_bin_dir, posixpath.basename(path)), path)
        for path in _ALL_ANDROID_BINS])
    with device.adb.PersistentShell(device.adb.GetDeviceSerial()) as pshell:
      pshell.RunCommand(_IN_BACKGROUND % ANDROID_TRACED)
      pshell.RunCommand(_IN_BACKGROUND % ANDROID_TRACED_PROBES, close=True)
    processes = set(p.name for p in device.ListProcesses(ANDROID_TRACED))
    assert ANDROID_TRACED in processes
    assert ANDROID_TRACED_PROBES in processes
    logging.warning('Perfetto tracing agent is set up.')

  @classmethod
  def IsSupported(cls, platform_backend):
    # TODO: Support other platforms.
    return platform_backend.GetOSName() == 'android'

  def _PersistentShell(self):
    serial = self._device.adb.GetDeviceSerial()
    return self._device.adb.PersistentShell(serial)

  def _TempFile(self, **kwargs):
    return device_temp_file.DeviceTempFile(self._device.adb, **kwargs)

  def StartAgentTracing(self, config, timeout):
    del timeout  # Unused.
    self._trace_config_temp_file = self._TempFile(suffix='.txt')
    self._trace_output_temp_file = self._TempFile(suffix='.pb',
                                                  dir=ANDROID_TRACES_DIR)
    self._device.WriteFile(
        self._trace_config_temp_file.name, ConfigToTextProto(config))
    cmd = [ANDROID_PERFETTO,
           '--config', self._trace_config_temp_file.name, '--txt',
           '--out', self._trace_output_temp_file.name]
    start_perfetto = ' '.join(cmd_helper.SingleQuote(c) for c in cmd)
    with self._PersistentShell() as pshell:
      pshell.RunCommand(_IN_BACKGROUND % start_perfetto, close=True)
    logging.warning('Started perfetto system tracing.')
    return True

  def StopAgentTracing(self):
    self._device.RunShellCommand(
        [ANDROID_TRIGGER_PERFETTO, 'stop_telemetry_system_tracing'],
        check_return=True)
    logging.warning('Stopped perfetto system tracing.')

  def CollectAgentTraceData(self, trace_data_builder, timeout=None):
    del timeout  # Unused.
    with trace_data_builder.OpenTraceHandleFor(
        trace_data.CHROME_TRACE_PART, suffix='.pb') as handle:
      pass
    self._device.PullFile(self._trace_output_temp_file.name, handle.name)
    self._trace_config_temp_file.close()
    self._trace_output_temp_file.close()
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
