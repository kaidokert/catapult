# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Tracing agent that captures cgroup information from /dev/cpuset on
# an Android device.

import stat
import logging
import py_utils

from devil.android import device_utils
from systrace import tracing_agents
from systrace import trace_result

# identify this as trace of cgroup state
TRACE_HEADER = 'CGROUP DUMP\n'

def add_options(parser): # pylint: disable=unused-argument
  return None

def try_create_agent(config):
  if config.target != 'android':
    return None
  if not config.atrace_categories:
    return None
  # 'sched' contains cgroup events
  if 'sched' not in config.atrace_categories:
    return None
  if config.from_file is not None:
    return None
  return AndroidCgroupAgent()

def get_config(options):
  return options

class AndroidCgroupAgent(tracing_agents.TracingAgent):
  def __init__(self):
    super(AndroidCgroupAgent, self).__init__()
    self._trace_data = ""

  def __repr__(self):
    return 'cgroup_data'

  @py_utils.Timeout(tracing_agents.START_STOP_TIMEOUT)
  def StartAgentTracing(self, config, timeout=None):
    self._config = config
    self._device_utils = device_utils.DeviceUtils(
        self._config.device_serial_number)
    self._trace_data += self._get_cgroup_info()
    return True

  @py_utils.Timeout(tracing_agents.START_STOP_TIMEOUT)
  def StopAgentTracing(self, timeout=None):
    return True

  @py_utils.Timeout(tracing_agents.GET_RESULTS_TIMEOUT)
  def GetResults(self, timeout=None):
    result = TRACE_HEADER + self._trace_data
    return trace_result.TraceResult('cgroupDump', result)

  def SupportsExplicitClockSync(self):
    return False

  def RecordClockSyncMarker(self, sync_id, did_record_sync_marker_callback):
    pass

  def _parse_proc_cgroups(self, subsys):
    for line in self._device_utils.ReadFile('/proc/cgroups').split('\n'):
      if line.startswith(subsys):
        return line.split()[1]
    return -1

  def _parse_cgroup_id(self, root):
    cgrp_id_dict = {}
    try:
      # use inode number as cgroup id before v5.5 kernel
      out = self._device_utils.RunShellCommand(['ls', '-i', root])
      for cgid in out:
        ino, cgrp = cgid.split()
        cgrp_id_dict[cgrp] = ino
    except:
      pass
    return cgrp_id_dict

  def _get_cgroup_info(self):
    data = []
    CGROUP_SUBSYS = 'cpuset'
    CGROUP_ROOT = '/dev/cpuset/'

    root_id = self._parse_proc_cgroups(CGROUP_SUBSYS)
    cgrp_id_dict = self._parse_cgroup_id(CGROUP_ROOT)

    for cgrp in self._device_utils.StatDirectory(CGROUP_ROOT):
      if not stat.S_ISDIR(cgrp['st_mode']):
        continue
      tasks_file = CGROUP_ROOT + cgrp['filename'] + '/tasks'
      tasks = self._device_utils.ReadFile(tasks_file).split('\n')
      cgrp_info = '/%s (root=%s id=%s) : ' % (cgrp['filename'], root_id,
                                              cgrp_id_dict[cgrp['filename']])
      data.append(cgrp_info  + ' '.join(tasks))
    return '\n'.join(data) + '\n'
