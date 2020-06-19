# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import posixpath
import time

from telemetry.internal.platform import tracing_agent
from telemetry.internal.util import binary_manager

from devil.android import device_temp_file
from devil.android.sdk import version_codes
import py_utils
from tracing.trace_data import trace_data


ANDROID_TRACES_DIR = '/data/misc/perfetto-traces'
ANDROID_TMP_DIR = '/data/local/tmp'
ANDROID_TRACED = 'traced'
ANDROID_TRACED_PROBES = 'traced_probes'
ANDROID_PERFETTO = 'perfetto'
_ALL_ANDROID_BINS = (
    ANDROID_TRACED,
    ANDROID_TRACED_PROBES,
    ANDROID_PERFETTO
)


class PerfettoTracingAgent(tracing_agent.TracingAgent):
  def __init__(self, platform_backend):
    super(PerfettoTracingAgent, self).__init__(platform_backend)
    self._device = platform_backend.device
    self._trace_config_temp_file = None
    self._trace_output_temp_file = None
    self._perfetto_pid = None
    self._perfetto_path = ANDROID_PERFETTO

    if self._device.build_version_sdk <= version_codes.Q:
      logging.info('Sideloading perfetto binaries to the device.')
      self._device.RunShellCommand(['mkdir', '-p', ANDROID_TRACES_DIR])
      perfetto_device_path = posixpath.join(ANDROID_TMP_DIR, ANDROID_PERFETTO)
      traced_device_path = posixpath.join(ANDROID_TMP_DIR, ANDROID_TRACED)
      traced_probes_device_path = posixpath.join(
          ANDROID_TMP_DIR, ANDROID_TRACED_PROBES)
      perfetto_local_path = binary_manager.FetchPath(
          'perfetto_monolithic_perfetto',
          'android',
          platform_backend.GetArchName())
      traced_local_path = binary_manager.FetchPath(
          'perfetto_monolithic_traced',
          'android',
          platform_backend.GetArchName())
      traced_probes_local_path = binary_manager.FetchPath(
          'perfetto_monolithic_traced_probes',
          'android',
          platform_backend.GetArchName())
      self._device.PushChangedFiles([
          (perfetto_local_path, perfetto_device_path),
          (traced_local_path, traced_device_path),
          (traced_probes_local_path, traced_probes_device_path),
      ])
      in_background = '</dev/null >/dev/null 2>&1 &'
      self._device.RunShellCommand(traced_device_path + in_background,
                                   shell=True)
      self._device.RunShellCommand(traced_probes_device_path + in_background,
                                   shell=True)
      self._perfetto_path = perfetto_device_path

    processes = set(p.name for p in self._device.ListProcesses())
    assert ANDROID_TRACED in processes
    assert ANDROID_TRACED_PROBES in processes
    logging.info('Perfetto tracing agent is set up.')

  @classmethod
  def IsSupported(cls, platform_backend):
    return platform_backend.GetOSName() == 'android'

  def _TempFile(self, **kwargs):
    return device_temp_file.DeviceTempFile(self._device.adb, **kwargs)

  def StartAgentTracing(self, config, timeout):
    del timeout  # Unused.
    self._trace_config_temp_file = self._TempFile(suffix='.txt',
                                                  dir=ANDROID_TMP_DIR)
    self._trace_output_temp_file = self._TempFile(suffix='.pftrace',
                                                  dir=ANDROID_TRACES_DIR)
    text_config = config.system_trace_config.GetTextConfig()
    self._device.WriteFile(self._trace_config_temp_file.name, text_config)
    start_perfetto = (
        'cat %s | %s --background --config - --txt --out %s' % (
            self._trace_config_temp_file.name,
            self._perfetto_path,
            self._trace_output_temp_file.name,
        )
    )
    stdout = self._device.RunShellCommand(start_perfetto, shell=True)
    self._perfetto_pid = int(stdout[0])
    logging.info('Started perfetto with pid %s.', self._perfetto_pid)
    return True

  def StopAgentTracing(self):
    self._device.RunShellCommand(['kill', str(self._perfetto_pid)])
    logging.info('Stopped Perfetto system tracing.')

  def CollectAgentTraceData(self, trace_data_builder, timeout=300):
    start_time = time.time()
    with trace_data_builder.OpenTraceHandleFor(
        trace_data.CHROME_TRACE_PART, suffix='.pb') as handle:
      pass

    def PerfettoStopped():
      for p in self._device.ListProcesses(ANDROID_PERFETTO):
        if p.pid == self._perfetto_pid:
          return False
      return True
    py_utils.WaitFor(PerfettoStopped, timeout)
    timeout -= time.time() - start_time

    self._device.PullFile(
        self._trace_output_temp_file.name, handle.name, timeout=timeout)
    self._trace_config_temp_file.close()
    self._trace_output_temp_file.close()
    self._trace_config_temp_file = None
    self._trace_output_temp_file = None
    self._perfetto_pid = None
    logging.info('Collected trace from Perfetto system tracing.')
