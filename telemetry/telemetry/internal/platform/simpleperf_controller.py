# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os

from telemetry.internal.util import binary_manager


class SimpleperfController(object):
  _device_profilers_dir = '/data/local/tmp/profilers'
  _device_out_file = '/data/local/tmp/perf.data'

  def __init__(self, process_name, periods, frequency):
    process_name, _, thread_name = process_name.partition(':')
    self._process_name = process_name
    self._thread_name = thread_name
    self._periods = periods
    self._frequency = max(1, min(4000, int(frequency)))
    self._browser = None
    self._device_simpleperf_path = None
    self._profiling_process = None
    self._have_results = False

  def _install_simpleperf(self, device, package):
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

  def _start_sampling(self):
    assert self._browser
    if not self._browser.supports_simpleperf:
      return
    if self._profiling_process is not None:
      return
    self._have_results = False
    browser = self._browser
    device = browser.device
    package = browser.package
    simpleperf_path = self._install_simpleperf(device, package)
    device.SetProp('security.perf_harden', '0')

    processes = [p for p in browser.processes if
                 browser.GetProcessName(p.name) == self._process_name]
    if len(processes) != 1:
      raise Exception('Found %d running processes with names matching "%s"' %
                      (len(processes), self._process_name))
    pid = processes[0].pid

    profile_cmd = [simpleperf_path, 'record', '-g',
                   '-f', str(self._frequency),
                   '-o', self._device_out_file]

    if self._thread_name:
      threads = [t for t in device.ListProcesses(pid=pid, list_threads=True)
                 if (t.ppid == pid and
                     browser.GetThreadType(t.name) == self._thread_name)]
      if len(threads) != 1:
        raise Exception('Found %d threads with names matching "%s"' %
                        (len(threads), self._thread_name))
      profile_cmd.extend(['-t', str(threads[0].pid)])
    else:
      profile_cmd.extend(['-p', str(pid)])
    self._profiling_process = device.adb.StartShell(profile_cmd)

  def _stop_sampling(self):
    if self._profiling_process is None:
      return
    proc = self._profiling_process
    self._profiling_process = None
    device = self._browser.device
    pidof_lines = device.RunShellCommand(['pidof', 'simpleperf'])
    if not pidof_lines:
      raise Exception('Could not get pid of running simpleperf process.')
    device.RunShellCommand(['kill', '-s', 'SIGINT', pidof_lines[0].strip()])
    proc.wait()
    self._have_results = True

  def DidStartBrowser(self, browser):
    assert self._browser is None
    self._browser = browser

  def DidStopBrowser(self):
    assert self._browser is not None
    self._browser = None

  def WillNavigate(self):
    if 'navigation' in self._periods:
      self._start_sampling()

  def DidNavigate(self):
    if 'interactions' not in self._periods:
      self._stop_sampling()

  def WillRunPageInteractions(self):
    if 'interactions' in self._periods:
      self._start_sampling()

  def DidRunPageInteractions(self):
    self._stop_sampling()

  def GetResults(self, artifact_gen):
    if self._have_results:
      self._have_results = False
      with artifact_gen('simpleperf', suffix='.perf.data') as fh:
        local_file = fh.name
        fh.close()
        self._browser.device.PullFile(self._device_out_file, local_file)
