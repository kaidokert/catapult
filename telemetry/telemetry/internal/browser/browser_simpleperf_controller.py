# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import os

from telemetry.internal.util import binary_manager
from telemetry.util import statistics

from devil.android.sdk import version_codes

class BrowserSimpleperfController(object):
  DEVICE_PROFILERS_DIR = '/data/local/tmp/profilers'
  DEVICE_OUT_FILE_PATTERN = '/data/local/tmp/%s-perf.data'

  def __init__(self, process_name, periods, frequency):
    process_name, _, thread_name = process_name.partition(':')
    self._process_name = process_name
    self._thread_name = thread_name
    self._periods = periods
    self._frequency = statistics.Clamp(int(frequency), 1, 4000)
    self._browser = None
    self._device_simpleperf_path = None
    self._device_results = []

  def _InstallSimpleperf(self):
    if self._device_simpleperf_path is None:
      device = self._browser.device
      package = self._browser.package
      package_arch = device.GetPackageArchitecture(package) or 'armeabi-v7a'
      host_path = binary_manager.FetchPath(
          'simpleperf', package_arch, 'android')
      if not host_path:
        raise Exception('Could not get path to simpleperf executable on host.')
      device_path = os.path.join(self.DEVICE_PROFILERS_DIR,
                                 package_arch,
                                 'simpleperf')
      device.PushChangedFiles([(host_path, device_path)])
      self._device_simpleperf_path = device_path

  def _SimpleperfSupported(self):
    if not self._browser.device:
      return False
    version = getattr(self._browser.device, 'build_version_sdk', -1)
    return version >= version_codes.NOUGAT

  @staticmethod
  def _ThreadsForProcess(device, pid):
    if device.build_version_sdk >= version_codes.OREO:
      pid_regex = (
          '^[[:graph:]]\\{1,\\}[[:blank:]]\\{1,\\}%s[[:blank:]]\\{1,\\}' % pid)
      ps_cmd = "ps -T -e | grep '%s'" % pid_regex
      ps_output_lines = device.RunShellCommand(
          ps_cmd, shell=True, check_return=True)
    else:
      ps_cmd = ['ps', '-p', pid, '-t']
      ps_output_lines = device.RunShellCommand(ps_cmd, check_return=True)
    result = []
    for l in ps_output_lines:
      fields = l.split()
      if fields[2] == pid:
        continue
      result.append((fields[2], fields[-1]))
    return result

  def DidStartBrowser(self, browser):
    assert self._browser is None
    self._browser = browser
    if self._SimpleperfSupported():
      self._InstallSimpleperf()

  @contextlib.contextmanager
  def SamplePeriod(self, period):
    assert self._browser
    profiling_process = None
    out_file = self.DEVICE_OUT_FILE_PATTERN % period

    if self._SimpleperfSupported():
      assert self._device_simpleperf_path

      browser = self._browser
      device = browser.device

      # Necessary for profiling
      # https://android-review.googlesource.com/c/platform/system/sepolicy/+/234400
      device.SetProp('security.perf_harden', '0')

      processes = [p for p in browser.processes if
                   browser.GetProcessName(p.name) == self._process_name]
      if len(processes) != 1:
        raise Exception('Found %d running processes with names matching "%s"' %
                        (len(processes), self._process_name))
      pid = processes[0].pid

      profile_cmd = [self._device_simpleperf_path, 'record',
                     '-g', # enable call graphs based on dwarf debug frame
                     '-f', str(self._frequency),
                     '-o', out_file]

      if self._thread_name:
        threads = [t for t in self._ThreadsForProcess(device, str(pid))
                   if browser.GetThreadType(t[1]) == self._thread_name]
        if len(threads) != 1:
          raise Exception('Found %d threads with names matching "%s"' %
                          (len(threads), self._thread_name))
        profile_cmd.extend(['-t', threads[0][0]])
      else:
        profile_cmd.extend(['-p', str(pid)])
      profiling_process = device.adb.StartShell(profile_cmd)

    yield

    if profiling_process is not None:
      device = self._browser.device
      pidof_lines = device.RunShellCommand(['pidof', 'simpleperf'])
      if not pidof_lines:
        raise Exception('Could not get pid of running simpleperf process.')
      device.RunShellCommand(['kill', '-s', 'SIGINT', pidof_lines[0].strip()])
      profiling_process.wait()
      self._device_results.append((period, out_file))

  def GetResults(self, artifact_gen, page_name):
    for period, device_file in self._device_results:
      prefix = '%s-%s-' % (page_name, period)
      with artifact_gen('simpleperf', prefix=prefix, suffix='.perf.data') as fh:
        local_file = fh.name
        fh.close()
        self._browser.device.PullFile(device_file, local_file)
    self._device_results = []
