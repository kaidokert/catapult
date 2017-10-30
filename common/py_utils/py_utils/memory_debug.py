#!/usr/bin/env python
# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import heapq
import logging
import os
import psutil
import sys


BYTE_UNITS = ['B', 'KiB', 'MiB', 'GiB']


def FormatBytes(value):
  def GetValueAndUnit(value):
    for unit in BYTE_UNITS[:-1]:
      if abs(value) < 1024.0:
        return value, unit
      value /= 1024.0
    return value, BYTE_UNITS[-1]

  return '%.1f %s' % GetValueAndUnit(value)


def _GetProcessInfo(p):
  return p.as_dict(attrs=['pid', 'name', 'memory_info'])


def _LogProcessInfo(pinfo, level):
  pinfo['rss_fmt'] = FormatBytes(pinfo['memory_info'].rss)
  logging.log(level, '- %(rss_fmt)s (pid=%(pid)s) %(name)s', pinfo)


def LogHostMemoryUsage(top_n=10, level=logging.INFO):
  if psutil.version_info < (2, 0):
    logging.warning('psutil %s too old, upgrade to version 2.0 or higher'
                    ' for memory usage information.', psutil.__version__)
    return

  mem = psutil.virtual_memory()
  logging.log(level, 'Used %s out of %s memory available.',
              FormatBytes(mem.used), FormatBytes(mem.total))
  logging.log(level, 'Top %s memory consumers:', top_n)
  pinfos = (_GetProcessInfo(p) for p in psutil.process_iter())
  pinfos = heapq.nlargest(top_n, pinfos, key=lambda p: p['memory_info'].rss)
  for pinfo in pinfos:
    _LogProcessInfo(pinfo, level)
  logging.log(level, 'Current process:')
  pinfo = _GetProcessInfo(psutil.Process(os.getpid()))
  _LogProcessInfo(pinfo, level)


def main():
  logging.basicConfig(level=logging.INFO)
  LogHostMemoryUsage()


if __name__ == '__main__':
  sys.exit(main())
