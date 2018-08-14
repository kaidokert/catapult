# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Helper function to run the benchmark.
"""
import os
import subprocess

from long_term_health import utils


def RunBenchmark(path_to_apk, run_label):
  """Install the APK and run the benchmark on it.

  Args:
    path_to_apk(string): the *relative* path to the APK
    run_label(string): the name of the directory to contains all the output
    from this run
  """
  milestone_num = 'M%s' % path_to_apk.split('/')[-1].split('.')[0]
  subprocess.call(['adb', 'install', '-r', '-d', path_to_apk])
  subprocess.call([os.path.join(utils.CHROMIUM_SRC, 'tools',
                                'perf', 'run_benchmark'),
                   '--browser=android-system-chrome',
                   '--pageset-repeat=1',  # could remove this later
                   # TODO(wangge):not sure if we should run in compatibility
                   # mode even for the later version, probably add a check in
                   # caller to determine if we should run it in compatibility
                   # mode and add an argument `run_in_compatibility_mode` to
                   # the `RunBenchmark` function
                   '--compatibility-mode',
                   '--story-filter=wikipedia',  # could remove this
                   # thinking of adding an argument to the tool to set this
                   '--output-dir=%s' % os.path.join(
                       utils.APP_ROOT, 'results', run_label,
                       milestone_num),
                   # thinking of adding an argument to the tool to set this too
                   'system_health.memory_mobile'])
