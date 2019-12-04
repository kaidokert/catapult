# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import logging
import os
import posixpath

from devil.android import device_signal
from devil.android import device_temp_file
from devil.utils import cmd_helper


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
duration_ms: {duration_ms}
"""


class PerfettoService(object):
  BINARIES = ('traced', 'traced_probes', 'perfetto')
  ANDROID_BIN_DIR = '/data/local/tmp'
  ANDROID_TRACES_DIR = '/data/misc/perfetto-traces'

  def __init__(self, platform_backend, host_bin_dir):
    assert platform_backend.GetOSName() == 'android', (
        'Telemetry only supports perfetto on Android at the moment')
    self._device = platform_backend.device
    self._host_device_pairs = [
        (os.path.join(host_bin_dir, n), posixpath.join(self.ANDROID_BIN_DIR, n))
        for n in self.BINARIES]
    self._pshell = None
    self._trace_config_temp_file = None
    self._trace_output_temp_file = None

  @property
  def traced_bin(self):
    return self._host_device_pairs[0][1]

  @property
  def traced_probes_bin(self):
    return self._host_device_pairs[1][1]

  @property
  def perfetto_bin(self):
    return self._host_device_pairs[2][1]

  def _PersistentShell(self):
    serial = self._device.adb.GetDeviceSerial()
    return self._device.adb.PersistentShell(serial)

  def _TempFile(self, **kwargs):
    return device_temp_file.DeviceTempFile(self._device.adb, **kwargs)

  def SetUp(self):
    """Install and start required perfetto binaries."""
    self._device.KillAll(self.traced_bin, exact=True, quiet=True)
    self._device.KillAll(self.traced_probes_bin, exact=True, quiet=True)
    self._device.KillAll(self.perfetto_bin, exact=True, quiet=True)
    self._device.PushChangedFiles(self._host_device_pairs)
    with self._PersistentShell() as pshell:
      pshell.RunCommand(_IN_BACKGROUND % self.traced_bin)
      pshell.RunCommand(_IN_BACKGROUND % self.traced_probes_bin, close=True)
    processes = set(p.name for p in self._device.ListProcesses(self.traced_bin))
    assert self.traced_bin in processes
    assert self.traced_probes_bin in processes

  def StartTracing(self, config):
    self._trace_config_temp_file = self._TempFile(suffix='.txt')
    self._trace_output_temp_file = self._TempFile(suffix='.pb',
                                                  dir=self.ANDROID_TRACES_DIR)
    self._device.WriteFile(
        self._trace_config_temp_file.name, ConfigToTextProto(config))
    cmd = [self.perfetto_bin,
           '--config', self._trace_config_temp_file.name, '--txt',
           '--out', self._trace_output_temp_file.name]
    start_perfetto = ' '.join(cmd_helper.SingleQuote(c) for c in cmd)
    with self._PersistentShell() as pshell:
      pshell.RunCommand(_IN_BACKGROUND % start_perfetto, close=True)
    logging.info('Started perfetto system tracing.')

  def StopTracing(self, results):
    self._device.KillAll(self.perfetto_bin, signum=device_signal.SIGINT,
                         exact=True, blocking=True)
    self._device.PullFile(self._trace_output_temp_file.name, 'trace.pb')
    self._trace_config_temp_file.close()
    self._trace_output_temp_file.close()
    self._trace_config_temp_file = None
    self._trace_output_temp_file = None


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
      duration_ms=30*60*1000)
  return trace_config
