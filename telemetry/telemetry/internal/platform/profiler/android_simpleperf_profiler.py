# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import signal

from telemetry.internal.backends.chrome import android_browser_finder
from telemetry.internal.platform.profiler import Profiler
from telemetry.internal.platform.android_platform_backend import AndroidPlatformBackend
from telemetry.internal.util import binary_manager

class AndroidSimpleperfProfiler(Profiler):
  """Runs simpleperf to profile a single thread on Android."""

  _process_patterns = {
      'browser': '',
      'renderer': ':sandboxed_process'
  }

  _thread_patterns = {
      'main': 'CrRendererMain',
      'compositor': 'Compositor'
  }

  _device_profilers_dir = '/data/local/tmp/profilers'

  def __init__(self, browser_backend, platform_backend, output_path, state,
               **kwargs):
    if not isinstance(platform_backend, AndroidPlatformBackend):
      raise Exception('simpleperf profiler is only for android.')
    super(AndroidSimpleperfProfiler, self).__init__(
        browser_backend, platform_backend, output_path, state)
    device = platform_backend.device
    simpleperf_path = self._install_simpleperf_for_package(
        device, browser_backend.package)
    out_file = '/data/local/tmp/%s.perf.data' % os.path.basename(
        self._output_path)
    profile_frequency = max(1, min(4000, int(kwargs.get('frequency', 1000))))
    process_name = kwargs.get('process', 'browser')
    if process_name not in self._process_patterns:
      raise Exception('Cannot run simpleperf on unknown process name "%s"'
                      % process_name)
    process_pattern = (browser_backend.package +
                       self._process_patterns[process_name])
    processes = device.ListProcesses(process_name=process_pattern)
    if len(processes) != 1:
      raise Exception('Found %d running processes with names matching "%s"' %
                      (len(processes), process_pattern))
    pid = processes[0].pid
    profile_cmd = [simpleperf_path, 'record', '-g',
                   '-f', str(profile_frequency),
                   '-o', out_file]
    if kwargs.get('thread'):
      thread_name = kwargs['thread']
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


    self._device = device
    self._out_file = out_file
    self._profiling_process = device.StartShellCommand(profile_cmd)

  @classmethod
  def name(cls):
    return 'simpleperf'

  @classmethod
  def is_supported(cls, browser_type):
    if browser_type == 'any':
      return android_browser_finder.CanFindAvailableBrowsers()
    return browser_type.startswith('android')

  def StopCollecting(self):
    # There's no obvious reason why we shouldn't SIGINT and then immediately
    # communicate() the profiler process and Pull() the file from the device.
    # However, experimentation shows that the profiling output file is not ready
    # immediately after the simpleperf process ends. Presumably, there is a
    # detached, backgrounded process that continues running long enough to
    # finish writing output. It's necessary to wait a short time (seems to be
    # less than three seconds) for that other process to finish before pulling
    # the file from the device.  So, we just signal the process here, and wait
    # until CollectProfile (which runs much later) to pull the result.
    if self._profiling_process:
      self._profiling_process.send_signal(signal.SIGINT)

  def CollectProfile(self):
    if self._profiling_process:
      self._profiling_process.communicate()
      self._profiling_process = None
      local_file = "%s.perf.data" % self._output_path
      self._device.PullFile(self._out_file, local_file)
      return [local_file]

  @classmethod
  def _install_simpleperf_for_package(cls, device, package):
    dumpsys_lines = device.GetDumpsys(package, 'primaryCpuAbi')
    package_arch = 'armeabi-v7a'
    if len(dumpsys_lines):
      _, _, package_arch = dumpsys_lines[-1].rstrip().partition('=')
    host_path = binary_manager.FetchPath('simpleperf', package_arch, 'android')
    if not host_path:
      raise Exception('Could not get path to simpleperf executable on host.')
    device_path = os.path.join(cls._device_profilers_dir,
                               package_arch,
                               'simpleperf')
    device.PushChangedFiles([(host_path, device_path)])
    return device_path
