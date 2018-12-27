# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import base64
import contextlib
import json
import logging
import os
import tempfile
import time

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
    p.communicate()
    if p.returncode < 0:
      raise Exception('Invalid perf record options were provided')

  def _KillPerfProcess(self):
    pidof_line = self._platform_backend.RunCommand(
        ['pidof', self.PERF_PATH]).strip()
    pidof_lines = pidof_line.split()
    if not pidof_lines:
      raise Exception('Could not get pid of the running perf process.')
    self._platform_backend.RunCommand(['kill', '-s', 'SIGTERM', pidof_lines[0]])

  @contextlib.contextmanager
  def SampleSession(self, story_name, action_runner):
    if not self._start_profiler:
      yield
      return
    (fd, outfile) = tempfile.mkstemp(".data", "perf", self._temp_dir)
    os.close(fd)
    platform_backend = action_runner.tab.browser._platform_backend
    profiling_process = platform_backend.StartCommand(
        self._perf_cmd + ['-o', outfile])
    start = time.time()
    try:
      yield
    except Exception as exc: # pylint: disable=broad-except
      self._stats[story_name] = {'duration_ms': (time.time() - start) * 1000}
      try:
        self._KillPerfProcess()
      except Exception as perf_exc: # pylint: disable=broad-except
        logging.warning('_KillPerfProcess raised exception: %s("%s")',
                        type(perf_exc), perf_exc.message)
      finally:
        profiling_process.kill()
        raise exc
    self._stats[story_name] = {'duration_ms': (time.time() - start) * 1000}
    try:
      self._KillPerfProcess()
    except:
      profiling_process.kill()
      raise
    profiling_process.communicate()
    if profiling_process.returncode >= 0:
      self._device_file = outfile

  def IsEnabled(self):
    return self._start_profiler

  def GetResults(self, story_name, results):
    if story_name not in self._stats or not self._device_file:
      return
    if results.current_page_run.failed:
      self._stats[story_name]['run_status'] = 'failed'
    elif results.current_page_run.skipped:
      self._stats[story_name]['run_status'] = 'skipped'
    else:
      self._stats[story_name]['run_status'] = 'passed'
    # story_name can be base64 urlsafe decoded from the prefix, which ends with
    # '@@', of the .perf.data filename.
    prefix = (base64.urlsafe_b64encode(results.telemetry_info.benchmark_name)
              + "@@" + base64.urlsafe_b64encode(story_name) + "@@")
    with results.CreateArtifact(
        story_name, 'perf', prefix=prefix, suffix='.perf.data') as fh:
      local_file = fh.name
      fh.close()
      self._platform_backend.GetFile(self._device_file, local_file)
    self._device_file = None

  def WriteStatsJSON(self, results):
    stats = []
    for story_name, page_stats in self._stats.iteritems():
      e = {'benchmark_name': results.telemetry_info.benchmark_name,
           'story_name': story_name}
      e.update(page_stats)
      stats.append(e)
    with open(self._json_file, 'w') as json_pipe:
      print >> json_pipe, json.dumps(stats, indent=4, sort_keys=True,
                                     separators=(',', ': '))
