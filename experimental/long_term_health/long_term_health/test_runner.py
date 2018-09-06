# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Helper function to run the benchmark.

If there is any error when the job is running in swarming, please try following:
1. run `./tools/perf/fetch_benchmark_deps.py`
2. remove all the `*.sha1` files in `tools/perf/page_sets/data`
"""
import json
import os
import shutil
import subprocess
import time

from long_term_health import utils
from long_term_health.apk_finder import ChromeVersion


SWARMING_URL = 'https://chrome-swarming.appspot.com'
ISOLATE_URL = 'https://isolateserver.appspot.com'

CHROMIUM_ROOT = os.path.join(os.path.expanduser('~'), 'chromium', 'src')
MB = os.path.join(CHROMIUM_ROOT, 'tools', 'mb', 'mb.py')
SWARMING_CLIENT = os.path.join(CHROMIUM_ROOT, 'tools', 'swarming_client')
ISOLATE = os.path.join(SWARMING_CLIENT, 'isolate.py')
ISOLATE_SERVER = os.path.join(SWARMING_CLIENT, 'isolateserver.py')
SWARMING = os.path.join(SWARMING_CLIENT, 'swarming.py')
PATH_TO_APKS = os.path.join(CHROMIUM_ROOT, 'tools', 'perf', 'APKs')


def CheckComplete(task_id):
  return 'COMPLETE' in subprocess.check_output(
      [SWARMING, 'query', 'tasks/get_states?task_id=%s' % task_id,
       '--swarming', SWARMING_URL])


def GetResultFromSwarming(isolate_hash, isolate_server, output_dir):
  # download the json that contains the description of other files
  subprocess.call([ISOLATE_SERVER, 'download',
                   '--isolate-server', isolate_server,
                   '--file=%s' % isolate_hash, 'files.json',
                   '--target=%s' % output_dir,
                   '--cache=%s' % output_dir])  # set cache will clear the dir
  # download all the files
  with open(os.path.join(output_dir, 'files.json')) as json_:
    for file_, data_ in json.load(json_)['files'].iteritems():
      subprocess.call(
          [ISOLATE_SERVER, 'download', '--isolate-server', isolate_server,
           # `file_` looks like system_health.memory_mobile/benchmark_log.txt,
           # since we don't want to create a new directory, we remove the first
           # bit
           '--file=%s' % data_['h'], file_.split('/')[-1],
           '--target=%s' % output_dir,
          ])


def IncludeAPKInIsolate(apk_path):
  apk_dir_path = os.path.join(CHROMIUM_ROOT, 'tools', 'perf', 'swarming_apk')
  apk_name = apk_path.split('/')[-1]
  if os.path.isdir(apk_dir_path):
    shutil.rmtree(apk_dir_path)
  os.mkdir(apk_dir_path)
  shutil.copyfile(apk_path, os.path.join(apk_dir_path, apk_name))
  # relative path to be used when starting swarming job
  return os.path.join('..', '..', 'tools', 'perf', 'swarming_apk', apk_name)


def RunBenchmarkOnSwarming(path_to_apk):
  """Function to trigger the swarming job.

  This function will trigger the swarming job by first inlclude the apk in the
  `tools/perf` directory, then create an isolate, upload the isolate, then
  trigger the swarming job using the isolate.

  Args:
    path_to_apk(string): the path to the Clank APK

  Returns:
    string: task hash
  """
  isolated_apk_path = IncludeAPKInIsolate(path_to_apk)
  # TODO(wangge): need to make it work even if there is no `out/Debug`
  # generate isolate for the task,
  subprocess.call([MB, 'isolate', os.path.join(
      CHROMIUM_ROOT, 'out', 'Debug'), 'performance_test_suite'])
  # upload the isolate to the isolate server
  isolate_output = subprocess.check_output(
      [ISOLATE, 'archive',
       '-I', ISOLATE_URL,
       '-s', os.path.join(
           CHROMIUM_ROOT, 'out', 'Debug', 'performance_test_suite.isolated')])
  # trigger the swarming job using the isolate hash
  task_output = subprocess.check_output(
      [SWARMING, 'trigger',
       # select which swarming server to use
       '--swarming', SWARMING_URL,
       # select which isolate server to use
       '--isolate-server', ISOLATE_URL,
       '--priority', '25',
       # set the task name
       '--task-name', 'test run by wangge@',
       # select the bot criteria
       '--dimension', 'pool', 'chrome.tests.pinpoint',
       '--dimension', 'os', 'Android',
       '--dimension', 'device_os_flavor', 'aosp',
       # the isolate hash that is to be used, code is to get the isolate hash
       '--isolated', str(isolate_output.split(' ')[0]),
       # select the benchmark name
       '--', '--benchmarks', 'system_health.memory_mobile',
       '--story-filter', 'wikipedia', '--pageset-repeat', '1',
       '--compatibility-mode=no-field-trials',
       '--compatibility-mode=ignore-certificate-errors',
       '--compatibility-mode=legacy-command-line-path',
       '--compatibility-mode=gpu-benchmarking-fallbacks',
       '--browser', 'exact', '--device', 'android',
       '--browser-executable', isolated_apk_path,
       '--upload-results', '--output-format', 'histograms',
       '--results-label', 'Test Run 1',
       '--isolated-script-test-output', '${ISOLATED_OUTDIR}/output.json',
       '--isolated-script-test-perf-output',
       '${ISOLATED_OUTDIR}/perftest-output.json'
      ])
  return task_output.split('/')[-1].strip()  # return task hash


def CollectResults(version_task_id_table, run_label):
  """Collect the result from swarming if there is task id in the table.

  This function repeatedly checks with the swarming server to see if the
  task has completed, if yes it will collect the result and set the task id to
  None. The function terminates once all the task id are None, i.e. all
  results are collected.

  Args:
    version_task_id_table(string, string dict): the mapping table for the
    milestone number and the task id, the task id will all be None in the case
    when the benchmark is running locally

    run_label(string): the name for the output directory, user supplies this
    when invoking the tool
  """
  while True:
    if all([id_ is None for id_ in version_task_id_table.values()]):
      print 'Job completed! Well done!'
      return

    for version, task_id in version_task_id_table.iteritems():
      if CheckComplete(task_id):
        output = subprocess.check_output(
            [SWARMING, 'query', 'task/%s/result' % task_id,
             '--swarming', SWARMING_URL])
        output_isolate_data = json.loads(output)['outputs_ref']
        GetResultFromSwarming(
            output_isolate_data['isolated'],
            output_isolate_data['isolatedserver'], os.path.join(
                utils.APP_ROOT, 'results', run_label, version))
        version_task_id_table[version] = None

    print 'Waiting for job to complete.'
    print version_task_id_table
    time.sleep(30)


def RunBenchmarkLocally(path_to_apk, run_label):
  """Install the APK and run the benchmark on it.

  Args:
    path_to_apk(string): the *relative* path to the APK
    run_label(string): the name of the directory to contain all the output
    from this run
  """
  # `path_to_apk` is similar to `./out/59.0.3071.132_arm_MonochromeStable.apk`
  chrome_version = ChromeVersion(path_to_apk.split('/')[-1].split('_')[0])
  subprocess.call(['adb', 'install', '-r', '-d', path_to_apk])
  subprocess.call([os.path.join(utils.CHROMIUM_SRC, 'tools',
                                'perf', 'run_benchmark'),
                   '--browser=android-system-chrome',
                   '--pageset-repeat=1',  # could remove this later
                   '--results-label=%s' % str(chrome_version),
                   # TODO(wangge):not sure if we should run in compatibility
                   # mode even for the later version, probably add a check in
                   # caller to determine if we should run it in compatibility
                   # mode and add an argument `run_in_compatibility_mode` to
                   # the `RunBenchmark` function
                   '--compatibility-mode=no-field-trials',
                   '--compatibility-mode=ignore-certificate-errors',
                   '--compatibility-mode=legacy-command-line-path',
                   '--compatibility-mode=gpu-benchmarking-fallbacks',
                   '--story-filter=wikipedia',  # could remove this
                   # thinking of adding an argument to the tool to set this
                   '--output-dir=%s' % os.path.join(
                       utils.APP_ROOT, 'results', run_label,
                       str(chrome_version.milestone)),
                   # thinking of adding an argument to the tool to set this too
                   'system_health.memory_mobile'])


def RunBenchmark(path_to_apk, run_label, use_swarming):
  if use_swarming:
    return RunBenchmarkOnSwarming(path_to_apk)
  else:
    RunBenchmarkLocally(path_to_apk, run_label)
    # This is not strictly required, but I am trying to make it more explicit
    return None
