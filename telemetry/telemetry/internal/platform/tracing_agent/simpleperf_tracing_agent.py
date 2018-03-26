# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os

from devil.android.sdk import version_codes
from telemetry.internal.platform import android_platform_backend
from telemetry.internal.platform import tracing_agent
from telemetry.internal.util import binary_manager


class SimpleperfTracingAgent(tracing_agent.TracingAgent):

  _process_patterns = {
      'browser': '',
      'renderer': ':sandboxed_process'
  }

  _thread_patterns = {
      'main': 'CrRendererMain',
      'compositor': 'Compositor'
  }

  _device_profilers_dir = '/data/local/tmp/profilers'

  def __init__(self, platform_backend):
    if not isinstance(platform_backend,
                      android_platform_backend.AndroidPlatformBackend):
      raise Exception('simpleperf tracing is only for Android.')
    super(SimpleperfTracingAgent, self).__init__(platform_backend)
    self._device_simpleperf_path = None
    self._out_file = None
    self._profiling_process = None

  @classmethod
  def IsSupported(cls, platform_backend):
    return (platform_backend.GetOSName() == 'android' and
            platform_backend.device.build_version_sdk >=
            version_codes.LOLLIPOP)

  def StartAgentTracing(self, config, timeout):
    return True

  def StopAgentTracing(self):
    if self.IsTracing:
      self._stop_tracing()

  def CollectAgentTraceData(self, trace_data_builder, timeout=None):
    pass

  def StartAgentNavigationTracing(self, app, config, timeout):
    if not config.enable_simpleperf or not config.trace_navigation:
      return
    if self.IsTracing:
      return
    self._start_tracing(app, config, timeout)

  def StopAgentNavigationTracing(self, config):
    if self.IsTracing and not config.trace_interactions:
      self._stop_tracing()

  def StartAgentInteractionTracing(self, app, config, timeout):
    if not config.enable_simpleperf or not config.trace_interactions:
      return
    if self.IsTracing:
      return
    self._start_tracing(app, config, timeout)

  def StopAgentInteractionTracing(self, config):
    if self.IsTracing:
      self._stop_tracing()

  def CollectIntervalTracingArtifacts(self, artifact_gen):
    if self.IsTracing:
      self._stop_tracing()
    if self._out_file:
      with artifact_gen('profile', suffix='.perf.data') as fh:
        local_file = fh.name
        fh.close()
        self._platform_backend.device.PullFile(self._out_file, local_file)

  @property
  def IsTracing(self):
    return self._profiling_process is not None

  def _install_simpleperf_for_package(self, device, package):
    if self._device_simpleperf_path is None:
      package_arch = device.GetPackageArchitecture(package) or 'armeabi-v7a'
      host_path = binary_manager.FetchPath(
          'simpleperf', package_arch, 'android')
      if not host_path:
        raise Exception('Could not get path to simpleperf executable on host.')
      device_path = os.path.join(self._device_profilers_dir,
                                 package_arch,
                                 'simpleperf')
      device.PushChangedFiles([(host_path, device_path)])
      self._device_simpleperf_path = device_path
    return self._device_simpleperf_path

  def _start_tracing(self, app, config, _):
    if not hasattr(app, 'package') or not app.package:
      raise Exception('Cannot get package name from app')
    device = self._platform_backend.device
    simpleperf_path = self._install_simpleperf_for_package(device, app.package)
    device.SetProp('security.perf_harden', '0')
    profile_frequency = (
        max(1, min(4000, config.simpleperf_config.sample_frequency)))
    process_name = config.simpleperf_config.profile_process
    if process_name not in self._process_patterns:
      raise Exception('Cannot run simpleperf on unknown process name "%s"'
                      % process_name)
    process_pattern = app.package + self._process_patterns[process_name]
    processes = device.ListProcesses(process_name=process_pattern)
    if len(processes) != 1:
      raise Exception('Found %d running processes with names matching "%s"' %
                      (len(processes), process_pattern))
    self._out_file = device.RunShellCommand(
        ['mktemp', '-p', '/data/local/tmp'])[0].strip()
    profile_cmd = [simpleperf_path, 'record', '-g',
                   '-f', str(profile_frequency),
                   '-o', self._out_file]
    pid = processes[0].pid
    if config.simpleperf_config.profile_thread:
      thread_name = config.simpleperf_config.profile_thread
      if thread_name not in self._thread_patterns:
        raise Exception('Cannot run simpleperf on unknown thread name "%s"'
                        % thread_name)
      thread_pattern = self._thread_patterns[thread_name]
      tid = None
      for line in device.RunShellCommand(['ps', '-p', str(pid), '-t']):
        if line.split()[-1].startswith(thread_pattern):
          tid = line.split()[1]
      if tid is None:
        raise Exception('No "%s" thread associated with "%s" process.' %
                        (thread_name, process_name))
      profile_cmd.extend(['-t', tid])
    else:
      profile_cmd.extend(['-p', str(pid)])
    self._profiling_process = device.adb.StartShellCommand(profile_cmd)

  def _stop_tracing(self):
    if self._profiling_process:
      proc = self._profiling_process
      self._profiling_process = None
      device = self._platform_backend.device
      pidof_lines = device.RunShellCommand(['pidof', 'simpleperf'])
      if not pidof_lines:
        raise Exception('Could not get pid of running simpleperf process.')
      device.RunShellCommand(['kill', '-s', 'SIGINT', pidof_lines[0].strip()])
      proc.wait()
