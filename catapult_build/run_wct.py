# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import subprocess
from catapult_build import run_dev_server_tests
from py_utils import binary_manager
from py_utils import dependency_util


def RunWct(base_dir, dep_dirs, chrome_channel='stable'):
  wct_bin = os.environ.get('WCT', 'wct')
  if os.system('which %s > /dev/null' % wct_bin):
    print 'FATAL ERROR: wct not found. Install it and add it to your path:'
    print 'cipd install -root ~/cipd infra/testing/wct/linux-amd64 prod'
    print 'export PATH=~/cipd:$PATH'
    return 1

  chrome_bin = run_dev_server_tests.GetLocalChromePath(None)
  if not chrome_bin:
    chrome_manager = binary_manager.BinaryManager([
        run_dev_server_tests.CHROME_BINARIES_CONFIG])
    arch, os_name = dependency_util.GetOSAndArchForCurrentDesktopPlatform()
    chrome_bin = chrome_manager.FetchPathWithVersion(
        'chrome_%s' % chrome_channel, arch, os_name)[0]

  command = [wct_bin, '-chrome', chrome_bin, '-base', base_dir]
  for dep in dep_dirs:
    command += ['-dep', dep]
  return subprocess.call(command)
