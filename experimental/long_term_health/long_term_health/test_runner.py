# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Helper function to run the benchmark.
"""
import json
import os
import shutil
import subprocess
import time

from long_term_health import utils
from long_term_health.apk_finder import ChromeVersion


SWARMING_URL = 'https://chrome-swarming.appspot.com'
ISOLATE_SERVER_URL = 'https://chrome-isolated.appspot.com'

CATAPULT_ROOT = os.path.normpath(os.path.join(utils.APP_ROOT, '..', '..'))
CHROMIUM_ROOT = os.path.normpath(os.path.join(CATAPULT_ROOT, '..', '..'))
MB = os.path.join(CHROMIUM_ROOT, 'tools', 'mb', 'mb.py')
SWARMING_CLIENT = os.path.join(CHROMIUM_ROOT, 'tools', 'swarming_client')
ISOLATE_SERVER_SCRIPT = os.path.join(SWARMING_CLIENT, 'isolateserver.py')
ISOLATE_SCRIPT = os.path.join(SWARMING_CLIENT, 'isolate.py')
SWARMING_SCRIPT = os.path.join(SWARMING_CLIENT, 'swarming.py')
PATH_TO_APKS = os.path.join(CHROMIUM_ROOT, 'tools', 'perf', 'swarming_apk')

RESULT_FILE_NAME = 'perf_results.json'


def IncludeAPKInIsolate(apk_path):
  apk_name = os.path.basename(apk_path)
  if not os.path.isdir(PATH_TO_APKS):
    os.mkdir(PATH_TO_APKS)
  shutil.copyfile(apk_path, os.path.join(PATH_TO_APKS, apk_name))
  # relative path to be used when starting swarming job
  return os.path.join('..', '..', 'tools', 'perf', 'swarming_apk', apk_name)


def GenerateIsolate(out_dir_path, target_name):
  # TODO(wangge): need to make it work even if there is no `out/Debug`
  subprocess.call([MB, 'isolate', out_dir_path, target_name])


def UploadIsolate(isolated_path):
  return subprocess.check_output(
      [ISOLATE_SCRIPT, 'archive', '-I', ISOLATE_SERVER_URL,
       '-s', isolated_path])


def TriggerSwarmingJob(isolate_hash, isolated_apk_path):
  """Function to trigger the swarming job.

  Args:
    isolate_hash(string): the isolate hash given by the isolate server
    isolated_apk_path(string): the *relative* path to the APK in the isolate

  Returns:
    string: swarming job task hash
  """
  # set the swarming task attribute
  swarming_trigger_options = [
      SWARMING_SCRIPT, 'trigger',
      # select which swarming server to use
      '--swarming', SWARMING_URL,
      # select which isolate server to use
      '--isolate-server', ISOLATE_SERVER_URL,
      '--priority', '25',
      # set the task name
      '--task-name', 'long_term_health_task',
      # the isolate hash that is to be used
      '--isolated', isolate_hash,
  ]
  # select the bot criteria
  bot_dimension_options = [
      '--dimension', 'pool', 'chrome.tests.pinpoint',
      '--dimension', 'os', 'Android',
      '--dimension', 'device_os_flavor', 'aosp',
  ]
  # options provided to the `run_benchmark` script
  run_benchmark_options = [
      'system_health.memory_mobile',
      '--pageset-repeat', '1',
      '--compatibility-mode=no-field-trials',
      '--compatibility-mode=ignore-certificate-errors',
      '--compatibility-mode=legacy-command-line-path',
      '--compatibility-mode=gpu-benchmarking-fallbacks',
      '--browser', 'exact', '--device', 'android',
      '--browser-executable', isolated_apk_path,
      '--upload-results', '--output-format', 'histograms',
      '--results-label', 'Test Run 1',
  ]
  output_options = [
      '--isolated-script-test-output', '${ISOLATED_OUTDIR}/output.json',
      '--isolated-script-test-perf-output',
      '${ISOLATED_OUTDIR}/perftest-output.json'
  ]
  task_output = subprocess.check_output(
      swarming_trigger_options +
      bot_dimension_options + ['--', '--benchmarks'] +
      run_benchmark_options + output_options)
  return task_output.split('/')[-1].strip()  # return task hash


def IsTaskCompleted(task_id):
  return 'COMPLETE' in subprocess.check_output(
      [SWARMING_SCRIPT, 'query', 'tasks/get_states?task_id=%s' % task_id,
       '--swarming', SWARMING_URL])


def GetResultFromSwarming(isolate_hash, output_dir, benchmark_name, shard_id):
  """Download `perf_results.json` in the given isolate hash.

  Args:
    isolate_hash(string): the output isolate hash given by the swarming server
    output_dir(string): the dir to put the downloaded files
    benchmark_name(string): the benchmark that we ran
    shard_id(int): the shard id
  """
  # download the json that contains the description of other files
  # do not use the `--cache`, it will clear the directory
  subprocess.check_call(
      [ISOLATE_SERVER_SCRIPT, 'download',
       '--isolate-server', ISOLATE_SERVER_URL,
       '--file=%s' % isolate_hash, 'files.json', '--target=%s' % output_dir,])

  # files.json looks like:
  # {...
  # 'files': {
  #   'system_health.memory_mobile/perf_results.json': {
  #     'h': hash_num
  #     }
  #   }
  # }
  with open(os.path.join(output_dir, 'files.json')) as data:
    result_json_hash = json.load(data)['files'][
        '%s/%s' % (benchmark_name, RESULT_FILE_NAME)]['h']
    subprocess.call(
        [ISOLATE_SERVER_SCRIPT, 'download',
         '--isolate-server', ISOLATE_SERVER_URL,
         '--file=%s' % result_json_hash, '%d_' % shard_id + RESULT_FILE_NAME,
         '--target=%s' % output_dir,
        ])

  os.remove(os.path.join(output_dir, 'files.json'))


def CollectResults(version_task_id_table, run_label, benchmark_name):
  """Collect the result from swarming if there is task id in the table.

  This function repeatedly checks with the swarming server to see if the
  task has completed, if yes it will collect the result and update the task
  state and output isolate hash. The function terminates once all the tasks are
  completed.

  Args:
    version_task_id_table(string, string dict): the mapping table for the
    milestone number and the swarming jobs info. It will be like the following:
       {'version1':
         [
           {'task_hash': hash_1,
            'completed': False,
            'results_isolate': None},
           {'task_hash': hash_2,
            'completed': True,
            'results_isolate': None},
            ...
         ],
        'version2': [...]}
    In the case of running locally, all the `completed` key will be set to True.

    run_label(string): the name for the output directory, user supplies this
    when invoking the tool

    benchmark_name(string): the name of the benchmark that you ran
  """
  while True:
    completed = True
    for version, tasks in version_task_id_table.iteritems():
      for shard_id, task in enumerate(tasks):
        if not task['completed']:
          if IsTaskCompleted(task['task_hash']):
            output = subprocess.check_output(
                [SWARMING_SCRIPT, 'query', 'task/%s/result' % task['task_hash'],
                 '--swarming', SWARMING_URL])
            output_isolate_data = json.loads(output)['outputs_ref']
            GetResultFromSwarming(
                output_isolate_data['isolated'],
                os.path.join(utils.APP_ROOT, 'results', run_label, version),
                benchmark_name,
                shard_id)
            task['results_isolate'] = output_isolate_data['isolated']
            task['completed'] = True
          else:
            completed = False
    if completed:
      break
    print 'Waiting for job to complete.'
    print version_task_id_table
    time.sleep(30)


def RunBenchmark(path_to_apk, run_label):
  """Install the APK and run the benchmark on it.

  Args:
    path_to_apk(string): the *relative* path to the APK
    run_label(string): the name of the directory to contains all the output
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
