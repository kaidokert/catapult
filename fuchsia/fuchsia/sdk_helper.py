# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import subprocess

CHROMIUM_SOURCE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir,
                  os.pardir))
SDK_ROOT = os.path.join(CHROMIUM_SOURCE_ROOT, 'third_party',
                          'fuchsia-sdk', 'sdk')

_LIST_DEVICES_TIMEOUT_SECS = 3

def findDevices():
    dev_finder_path = os.path.join(SDK_ROOT, 'tools', 'dev_finder')
    command = [dev_finder_path, 'list', '-full',
                 '-timeout', str(_LIST_DEVICES_TIMEOUT_SECS * 1000)]
    return subprocess.Popen(command,
                            stdout=subprocess.PIPE,
                            stderr=open(os.devnull, 'w'))

