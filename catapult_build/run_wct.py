# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import subprocess
import sys

from catapult_build import run_dev_server_tests
from py_utils import binary_manager
from py_utils import dependency_util

def _AddToPathIfNeeded(path):
  if path not in sys.path:
    sys.path.insert(0, path)

_CATAPULT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
_AddToPathIfNeeded(os.path.join(_CATAPULT_PATH, 'common', 'node_runner'))

from node_runner import node_util

NODE_MODULES = node_util.GetNodeModulesPath()
RUN_WCT = os.path.join(NODE_MODULES, '..', 'run-wct')


def RunWct(base_dir, dep_dirs, debug=False, chrome_channel='stable',
           prefix=''):
  chrome_bin = run_dev_server_tests.GetLocalChromePath(None)
  if not chrome_bin:
    chrome_manager = binary_manager.BinaryManager([
        run_dev_server_tests.CHROME_BINARIES_CONFIG])
    arch, os_name = dependency_util.GetOSAndArchForCurrentDesktopPlatform()
    chrome_bin = chrome_manager.FetchPathWithVersion(
        'chrome_%s' % chrome_channel, arch, os_name)[0]
    if not chrome_bin or os.system('which %s > /dev/null' % chrome_bin):
      print 'FATAL ERROR: chrome not found.'
      return 1

  command = [RUN_WCT]
  command += ['--chrome', chrome_bin]
  command += ['--base', base_dir]
  command += ['--prefix', prefix]
  if debug:
    command += ['--debug']
  for dep in dep_dirs:
    command += ['--dep', dep]
  logging.info('Starting WCT: %r', command)

  return subprocess.call(command)
