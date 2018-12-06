# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import json
import logging
import os
import subprocess
import tempfile
import time
import base64

__all__ = ['SystemWideProfilingController']

class SystemWideProfilingController(object):
  PERF_PATH = "/usr/bin/perf"

  def __init__(self, start_profiler, possible_browser, perf_options, output_dir,
      temp_dir):
    os_name = possible_browser._platform_backend.GetOSName()
    if os_name != 'chromeos':
      self._start_profiler = False
    else:
      self._start_profiler = start_profiler
    if not self._start_profiler:
      return
    self._platform_backend = possible_browser._platform_backend
    self._perf_cmd = [self.PERF_PATH, 'record', '-a'] + perf_options.split()
    self._PrepareHostForPerf()
    self._ValidatePerfCommand(self._perf_cmd)
    self._temp_dir = temp_dir
    self._device_file = None
    self._stats = {}
    self._json_file = os.path.join(os.path.realpath(output_dir),
                                   "system_wide_profiling_stats.json")

  def _PrepareHostForPerf(self):
    kptr_file = '/proc/sys/kernel/kptr_restrict'
    data = self._platform_backend.GetFileContents(kptr_file)
    if data.strip() != '0':
      self._platform_backend.PushContents('0', kptr_file)

  def _ValidatePerfCommand(self, perf_cmd):
    if " -- " in perf_cmd:
      raise Exception('Cannot pass a command to run to perf record')
    p = self._platform_backend.StartCommand(
        perf_cmd + ['-o', '/dev/null', '-- touch /tmp/temp'])
    p.wait()
    if p.returncode != 0:
      raise Exception('Invalid perf record options were provided')

  @contextlib.contextmanager
  def SampleSession(self, page_name, action_runner):
    if not self._start_profiler:
      yield
      return
    (fd, outfile) = tempfile.mkstemp(".data", "perf", self._temp_dir)
    os.close(fd)
    platform_backend = action_runner.tab.browser._platform_backend
    profiling_process = platform_backend.StartCommand(
        self._perf_cmd + ['-o', outfile])
    start = time.time()
    yield
    self._stats[page_name] = {'duration_ms': (time.time() - start) * 1000}
    pidof_line = platform_backend.RunCommand(['pidof', self.PERF_PATH]).strip()
    pidof_lines = pidof_line.split()
    if not pidof_lines:
      raise Exception('Could not get pid of running perf process.')
    platform_backend.RunCommand(['kill', '-s', 'SIGINT', pidof_lines[0]])
    profiling_process.wait()
    self._device_file = outfile

  def IsEnabled(self):
    return self._start_profiler

  def GetResults(self, page_name, results):
    if page_name not in self._stats or not self._device_file:
      return
    if results.current_page_run.failed:
      self._stats[page_name]['run_status'] = 'failed'
    elif results.current_page_run.skipped:
      self._stats[page_name]['run_status'] = 'skipped'
    else:
      self._stats[page_name]['run_status'] = 'passed'
    # page_name can be base64 urlsafe decoded from the prefix, which ends with
    # '@@', of the .perf.data filename.
    with results.CreateArtifact(
      page_name, 'perf', prefix=base64.urlsafe_b64encode(page_name)+"@@",
      suffix='.perf.data') as fh:
      local_file = fh.name
      fh.close()
      self._platform_backend.GetFile(self._device_file, local_file)
    self._device_file = None

  def WriteStatsJSON(self, results):
    stats = []
    for page_name, page_stats in self._stats.iteritems():
      e = {'benchmark_name': results.telemetry_info.benchmark_name,
           'page_name': page_name}
      e.update(page_stats)
      stats.append(e)
    with open(self._json_file, 'w') as json_pipe:
      print >> json_pipe, json.dumps(stats, indent=4, sort_keys=True,
                                     separators=(',', ': '))
