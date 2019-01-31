# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import logging
import os
import shutil
import tempfile
import textwrap
import urllib

from telemetry.internal.util import binary_manager
from telemetry.util import statistics

from devil.android.sdk import version_codes

__all__ = ['BrowserIntervalProfilingController']

class BrowserIntervalProfilingController(object):
  def __init__(self, possible_browser, process_name, periods, frequency,
               profiler_options):
    process_name, _, thread_name = process_name.partition(':')
    self._process_name = process_name
    self._thread_name = thread_name
    self._periods = periods
    self._frequency = statistics.Clamp(int(frequency), 1, 4000)
    self._platform_controller = None
    if periods:
      # Profiling other periods along with the whole_story_run period leads to
      # running multiple profiling processes at the same time. It is not
      # gauranteed that the correct profiling process will be terminated at the
      # end of a session when multiple profiling processes are running at the
      # same time.
      if len(periods) > 1 and 'whole_story_run' in periods:
        raise Exception('Cannot provide other periods along with'
                        ' whole_story_run.')
      self._platform_controller = self._CreatePlatformController(
          possible_browser, process_name, thread_name, profiler_options)

  @staticmethod
  def _CreatePlatformController(possible_browser, process_name, thread_name,
                                profiler_options):
    os_name = possible_browser._platform_backend.GetOSName()
    is_supported_android = os_name == 'android' and (
        possible_browser._platform_backend.device.build_version_sdk >=
        version_codes.NOUGAT)

    if (os_name != 'linux' and not is_supported_android
        and os_name != 'chromeos'):
      return None

    if os_name == 'chromeos':
      if process_name != 'system_wide':
        raise Exception(
            'Only system-wide profiling is supported on ChromeOS.'
            ' Got process name %s' % process_name)
      if thread_name != '':
        raise Exception(
            'Thread name should be empty for system-wide profiling on ChromeOS.'
            ' Got thread name %s' % thread_name)
      return _ChromeOSController(possible_browser, profiler_options)

    if profiler_options != '':
      raise Exception(
          'Additional arguments to the profiler is not supported on %s'
          % os_name)
    if process_name == 'system_wide':
      raise Exception(
          'System-wide profiling is not supported on %s' % os_name)

    if os_name == 'linux':
      possible_browser.AddExtraBrowserArg('--no-sandbox')
      return _LinuxController(possible_browser)
    elif is_supported_android:
      return _AndroidController(possible_browser)

  @contextlib.contextmanager
  def SamplePeriod(self, period, action_runner):
    if not self._platform_controller or period not in self._periods:
      yield
      return

    with self._platform_controller.SamplePeriod(
        period=period,
        action_runner=action_runner,
        process_name=self._process_name,
        thread_name=self._thread_name,
        frequency=self._frequency):
      yield

  def GetResults(self, page_name, file_safe_name, results):
    if self._platform_controller:
      self._platform_controller.GetResults(
          page_name, file_safe_name, results)


class _PlatformController(object):
  def SamplePeriod(self, period, action_runner):
    raise NotImplementedError()

  def GetResults(self, page_name, file_safe_name, results):
    raise NotImplementedError()


class _LinuxController(_PlatformController):
  def __init__(self, _):
    super(_LinuxController, self).__init__()
    self._temp_results = []

  @contextlib.contextmanager
  def SamplePeriod(self, period, action_runner, **_):
    (fd, out_file) = tempfile.mkstemp()
    os.close(fd)
    action_runner.ExecuteJavaScript(textwrap.dedent("""
        if (typeof chrome.gpuBenchmarking.startProfiling !== "undefined") {
          chrome.gpuBenchmarking.startProfiling("%s");
        }""" % out_file))
    yield
    action_runner.ExecuteJavaScript(textwrap.dedent("""
        if (typeof chrome.gpuBenchmarking.stopProfiling !== "undefined") {
          chrome.gpuBenchmarking.stopProfiling();
        }"""))
    self._temp_results.append((period, out_file))

  def GetResults(self, page_name, file_safe_name, results):
    for period, temp_file in self._temp_results:
      prefix = '%s-%s-' % (file_safe_name, period)
      with results.CreateArtifact(
          page_name, 'pprof', prefix=prefix, suffix='.profile.pb') as dest_fh:
        with open(temp_file, 'rb') as src_fh:
          shutil.copyfileobj(src_fh, dest_fh.file)
        os.remove(temp_file)
    self._temp_results = []


class _AndroidController(_PlatformController):
  DEVICE_PROFILERS_DIR = '/data/local/tmp/profilers'
  DEVICE_OUT_FILE_PATTERN = '/data/local/tmp/%s-perf.data'

  def __init__(self, possible_browser):
    super(_AndroidController, self).__init__()
    self._device = possible_browser._platform_backend.device
    self._device_simpleperf_path = self._InstallSimpleperf(possible_browser)
    self._device_results = []

  @classmethod
  def _InstallSimpleperf(cls, possible_browser):
    device = possible_browser._platform_backend.device
    package = possible_browser._backend_settings.package

    # Necessary for profiling
    # https://android-review.googlesource.com/c/platform/system/sepolicy/+/234400
    device.SetProp('security.perf_harden', '0')

    # This is the architecture of the app to be profiled, not of the device.
    package_arch = device.GetPackageArchitecture(package) or 'armeabi-v7a'
    host_path = binary_manager.FetchPath(
        'simpleperf', package_arch, 'android')
    if not host_path:
      raise Exception('Could not get path to simpleperf executable on host.')
    device_path = os.path.join(cls.DEVICE_PROFILERS_DIR,
                               package_arch,
                               'simpleperf')
    device.PushChangedFiles([(host_path, device_path)])
    return device_path

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

  def _StartSimpleperf(
      self, browser, out_file, process_name, thread_name, frequency):
    device = browser._platform_backend.device

    processes = [p for p in browser._browser_backend.processes
                 if (browser._browser_backend.GetProcessName(p.name)
                     == process_name)]
    if len(processes) != 1:
      raise Exception('Found %d running processes with names matching "%s"' %
                      (len(processes), process_name))
    pid = processes[0].pid

    profile_cmd = [self._device_simpleperf_path, 'record',
                   '-g', # Enable call graphs based on dwarf debug frame
                   '-f', str(frequency),
                   '-o', out_file]

    if thread_name:
      threads = [t for t in self._ThreadsForProcess(device, str(pid))
                 if (browser._browser_backend.GetThreadType(t[1]) ==
                     thread_name)]
      if len(threads) != 1:
        raise Exception('Found %d threads with names matching "%s"' %
                        (len(threads), thread_name))
      profile_cmd.extend(['-t', threads[0][0]])
    else:
      profile_cmd.extend(['-p', str(pid)])
    return device.adb.StartShell(profile_cmd)

  @contextlib.contextmanager
  def SamplePeriod(self, period, action_runner, **kwargs):
    profiling_process = None
    out_file = self.DEVICE_OUT_FILE_PATTERN % period
    process_name = kwargs.get('process_name', 'renderer')
    thread_name = kwargs.get('thread_name', 'main')
    frequency = kwargs.get('frequency', 1000)
    profiling_process = self._StartSimpleperf(
        action_runner.tab.browser,
        out_file,
        process_name,
        thread_name,
        frequency)
    yield
    device = action_runner.tab.browser._platform_backend.device
    pidof_lines = device.RunShellCommand(['pidof', 'simpleperf'])
    if not pidof_lines:
      raise Exception('Could not get pid of running simpleperf process.')
    device.RunShellCommand(['kill', '-s', 'SIGINT', pidof_lines[0].strip()])
    profiling_process.wait()
    self._device_results.append((period, out_file))

  def GetResults(self, page_name, file_safe_name, results):
    for period, device_file in self._device_results:
      prefix = '%s-%s-' % (file_safe_name, period)
      with results.CreateArtifact(
          page_name, 'simpleperf', prefix=prefix, suffix='.perf.data') as fh:
        local_file = fh.name
        fh.close()
        self._device.PullFile(device_file, local_file)
    self._device_results = []


class _ChromeOSController(_PlatformController):
  PERF_BINARY_PATH = '/usr/bin/perf'
  DEVICE_OUT_FILE_PATTERN = '/tmp/%s-perf.data'
  DEVICE_KPTR_FILE = '/proc/sys/kernel/kptr_restrict'
  def __init__(self, possible_browser, profiler_options):
    super(_ChromeOSController, self).__init__()
    if profiler_options == '':
      raise Exception('Profiler options must be provided to run the linux perf'
                      ' tool on ChromeOS.')
    self._platform_backend = possible_browser._platform_backend
    # Default to system-wide profile collection as only system-wide profiling
    # is supported on ChromeOS.
    self._perf_command = ([self.PERF_BINARY_PATH]
                          + profiler_options.split() + ['-a'])
    self._PrepareHostForProfiling()
    self._ValidatePerfCommand()
    self._device_results = []

  # _PrepareHostForProfiling updates DEVICE_KPTR_FILE file with the 0 value to
  # make kernel mappings available to the user.
  def _PrepareHostForProfiling(self):
    data = self._platform_backend.GetFileContents(self.DEVICE_KPTR_FILE)
    if data.strip() != '0':
      self._platform_backend.PushContents('0', self.DEVICE_KPTR_FILE)
    data = self._platform_backend.GetFileContents(self.DEVICE_KPTR_FILE)
    if data.strip() != '0':
      raise Exception('Couldn\'t modify the "%s" file on the ChromeOS device.'
                      % self.DEVICE_OUT_FILE_PATTERN)

  # _ValidatePerfCommand validates the arguments passed in the profiler options
  # and validates the command by running it on the device.
  def _ValidatePerfCommand(self):
    # Validate the arguments passed in the profiler options.
    if self._perf_command[1] != "record" and self._perf_command[1] != "stat":
      raise Exception(
          'Only the record and stat perf commands are allowed.'
          ' Got "%s" perf command.' % self._perf_command[1])

    if '-o' in self._perf_command:
      raise Exception(
          'Cannot pass the output filename flag in the profiler options.'
          ' Constructed command "%s".' % ' '.join(self._perf_command))

    if '--' in self._perf_command:
      raise Exception(
          'Cannot pass a command to run in the profiler options.'
          ' Constructed command "%s".' % ' '.join(self._perf_command))

    # Run and validate the final linux perf command.
    cmd = self._perf_command + ['-o', '/dev/null', '-- touch /tmp/temp']
    p = self._platform_backend.StartCommand(cmd)
    p.wait()
    if p.returncode != 0:
      raise Exception('Perf command validation failed.'
                      ' Executed command "%s" and got returncode %d'
                      % (cmd, p.returncode))

  # _StopProfiling checks if the SSH process is alive. If the SSH process is
  # alive, terminates the profiling process and returns true. If the SSH process
  # is not alive, the profiling process has exited prematurely so returns false.
  def _StopProfiling(self, ssh_process):
    # Poll the SSH process to check if the connection is still alive. If it is
    # alive, the returncode should not be set.
    ssh_process.poll()
    if ssh_process.returncode != None:
      logging.warning('Profiling process exited prematurely.')
      return False
    # Kill the profiling process directly. Terminating the SSH process doesn't
    # kill the profiling process.
    self._platform_backend.RunCommand(['killall', self.PERF_BINARY_PATH])
    ssh_process.wait()
    return True

  # SamplePeriod collects CPU profiles for the giving period.
  @contextlib.contextmanager
  def SamplePeriod(self, period, action_runner, **_):
    out_file = self.DEVICE_OUT_FILE_PATTERN % period
    platform_backend = action_runner.tab.browser._platform_backend
    ssh_process = platform_backend.StartCommand(
        self._perf_command + ['-o', out_file])
    ok = True
    try:
      yield
    except Exception as exc: # pylint: disable=broad-except
      ok = False
      raise exc
    finally:
      ok = ok and self._StopProfiling(ssh_process)
      self._device_results.append((period, out_file, ok))

  def _CreateArtifacts(self, page_name, file_safe_name, results):
    for period, device_file, ok in self._device_results:
      if not ok:
        continue
      prefix = '%s-%s-' % (file_safe_name, period)
      local_file = None
      with results.CreateArtifact(
          page_name, 'perf', prefix=prefix, suffix='.perf.data') as fh:
        local_file = fh.name
      self._platform_backend.GetFile(device_file, local_file)

  # GetResults creates artifacts for the perf.data files generated during a
  # successful story run.
  def GetResults(self, page_name, _, results):
    if results.current_page_run.ok:
      # Benchmark and story names are delimited by "@@" and ends with "@@".
      # These can derived from the .perf.data filename.
      file_safe_name = (
          urllib.quote(results.telemetry_info.benchmark_name, safe='')
          + "@@" + urllib.quote(page_name, safe='') + "@@")
      self._CreateArtifacts(page_name, file_safe_name, results)

    self._platform_backend.RunCommand(
        ['rm', '-f'] + [df for _, df, _ in self._device_results])
    self._device_results = []
