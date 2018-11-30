#!/usr/bin/env python
# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import heapq
import logging
import os
import sys

import psutil  # pylint: disable=import-error

from distutils import version  # pylint: disable=no-name-in-module
assert version.LooseVersion(psutil.__version__) >= version.LooseVersion('2.0')

BYTE_UNITS = ['B', 'KiB', 'MiB', 'GiB']


def FormatBytes(value):
  def GetValueAndUnit(value):
    for unit in BYTE_UNITS[:-1]:
      if abs(value) < 1024.0:
        return value, unit
      value /= 1024.0
    return value, BYTE_UNITS[-1]

  if value is not None:
    return '%.1f %s' % GetValueAndUnit(value)
  else:
    return 'N/A'


def _GetProcessInfo(p):
  pinfo = p.as_dict(attrs=['pid', 'name', 'memory_info'])
  pinfo['mem_rss'] = getattr(pinfo['memory_info'], 'rss', 0)
  return pinfo


def _LogProcessInfo(pinfo, level):
  pinfo['mem_rss_fmt'] = FormatBytes(pinfo['mem_rss'])
  logging.log(level, '%(mem_rss_fmt)s (pid=%(pid)s)', pinfo)


def LogHostMemoryUsage(top_n=10, level=logging.INFO):
  mem = psutil.virtual_memory()
  logging.log(level, 'Used %s out of %s memory available.',
              FormatBytes(mem.used), FormatBytes(mem.total))
  logging.log(level, 'Memory usage of top %i processes groups', top_n)
  pinfos_by_names = {}
  for p in psutil.process_iter():
    try:
      pinfo = _GetProcessInfo(p)
    except psutil.NoSuchProcess:
      logging.exception('process %s no longer exists', p)
      continue
    pname = pinfo['name']
    if pname not in pinfos_by_names:
      pinfos_by_names[pname] = {'name': pname, 'total_mem_rss': 0, 'pids': []}
    pinfos_by_names[pname]['total_mem_rss'] += pinfo['mem_rss']
    pinfos_by_names[pname]['pids'].append(str(pinfo['pid']))

  sorted_pinfo_groups = heapq.nlargest(
      top_n, pinfos_by_names.values(), key=lambda item: item['total_mem_rss'])
  for group in sorted_pinfo_groups:
    group['total_mem_rss_fmt'] = FormatBytes(group['total_mem_rss'])
    group['pids_fmt'] = ', '.join(group['pids'])
    logging.log(
        level, '- %(name)s - %(total_mem_rss_fmt)s - pids: %(pids)s', group)
  logging.log(level, 'Current process:')
  pinfo = _GetProcessInfo(psutil.Process(os.getpid()))
  _LogProcessInfo(pinfo, level)


def main():
  logging.basicConfig(level=logging.INFO)
  LogHostMemoryUsage()


if __name__ == '__main__':
  sys.exit(main())
