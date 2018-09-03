# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import subprocess
import tempfile

from catapult_build import run_dev_server_tests
from py_utils import binary_manager
from py_utils import dependency_util


def RunWct(base_dir, dep_dirs, chrome_channel='stable'):
  wct_bin = os.path.join(base_dir, 'bin/wct')#os.environ.get('WCT', 'wct')
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

  user_data_dir = tempfile.mkdtemp()

  command = [wct_bin]
  command += ['-chrome', chrome_bin]
  command += ['-dir', user_data_dir]
  command += ['-base', base_dir]
  #command += ['-persist']
  for dep in dep_dirs:
    command += ['-dep', dep]
  print command
  try:
    return subprocess.call(command)
  finally:
    try:
      shutil.rmtree(user_data_dir)
    except OSError as e:
      logging.error('Error cleaning up temp dirs %s and %s: %s',
                    tmpdir, user_data_dir, e)
