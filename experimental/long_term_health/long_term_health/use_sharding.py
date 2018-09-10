#!/usr/bin/env python
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import json
import os
import shutil
import subprocess
import time

# from long_term_health \
import utils


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


def GetBotId(task_hash):
  output = subprocess.check_output(
      [SWARMING, 'query', 'task/%s/result' % task_hash,
       '--swarming', SWARMING_URL])
  print output
  bot_dimensions = json.loads(output)['bot_dimensions']
  # bot_dimension looks like: [{'key': 'xx', 'value': ['x', 'x', ...]}, ...]
  return [d['value'][0] for d in bot_dimensions if d['key'] == 'id'][0]


def IncludeAPKInIsolate(apk_path):
  apk_dir_path = os.path.join(CHROMIUM_ROOT, 'tools', 'perf', 'swarming_apk')
  apk_name = apk_path.split('/')[-1]
  if os.path.isdir(apk_dir_path):
    shutil.rmtree(apk_dir_path)
  os.mkdir(apk_dir_path)
  shutil.copyfile(apk_path, os.path.join(apk_dir_path, apk_name))
  # relative path to be used when starting swarming job
  return os.path.join('..', '..', 'tools', 'perf', 'swarming_apk', apk_name)


def RunBenchmarkOnSwarming(path_to_apk, story_id, bot_id=None):
  """Function to trigger the swarming job.

  This function will trigger the swarming job by first include the apk in the
  `tools/perf` directory, then create an isolate, upload the isolate, then
  trigger the swarming job using the isolate.

  Args:
    path_to_apk(string): the path to the Clank APK
    story_id(int): the story id that is to be ran, starting with 0

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
  swarming_trigger_command = [
      SWARMING, 'trigger',
      # select which swarming server to use
      '--swarming', SWARMING_URL,
      # select which isolate server to use
      '--isolate-server', ISOLATE_URL,
      '--priority', '25',
      # set the task name
      '--task-name', 'test run by wangge@',
      # the isolate hash that is to be used, code is to get the isolate hash
      '--isolated', str(isolate_output.split(' ')[0]),
      # select the benchmark name

    ]
  # select the bot criteria
  bot_dimension_options = [
      '--dimension', 'pool', 'chrome.tests.pinpoint',
      '--dimension', 'os', 'Android',
      '--dimension', 'device_os_flavor', 'aosp',
  ]
  benchmark_options = [
      'system_health.memory_mobile',
      '--story-shard-begin-index', str(story_id),
      '--story-shard-end-index', str(story_id + 1),
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
  if bot_id is not None:
    bot_dimension_options += ['--dimension', 'id', bot_id]
  # trigger the swarming job using the isolate hash
  task_output = subprocess.check_output(
      swarming_trigger_command + bot_dimension_options + ['--', '--benchmarks',]
      + benchmark_options + output_options)
  print task_output
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
        print(output)
        GetResultFromSwarming(
            output_isolate_data['isolated'],
            output_isolate_data['isolatedserver'], os.path.join(
                utils.APP_ROOT, 'results', run_label, version))
        version_task_id_table[version] = None

    print 'Waiting for job to complete.'
    print version_task_id_table
    time.sleep(30)

# 1. fire up one job to run on swarming, which should only run story 1
# 2. fire up two jobs to run on swarming, which should only run story 1 but in
# different milestones, but the same bot. This requires 2 isolate. and keep a
# note of the bot id.
def main():
  apk_paths = ['/usr/local/google/home/wangge/chromium/src/third_party/catapult/experimental/long_term_health/out/52.0.2743.117_arm_ChromeStable.apk',
               '/usr/local/google/home/wangge/chromium/src/third_party/catapult/experimental/long_term_health/out/53.0.2785.157_arm_ChromeStable.apk']
  story_id = 0
  story_tasks_table = []
  for apk_path in apk_paths:
    if len(story_tasks_table) == story_id:
      story_tasks_table.append([RunBenchmarkOnSwarming(apk_path, story_id)])
      # time.sleep(5)  # this is necessary, because
    elif len(story_tasks_table) == story_id + 1:
      while True:  # maybe set a max retry number for this?
        try:
          bot_id = GetBotId(story_tasks_table[story_id][0])
          break
        except KeyError:
          time.sleep(5)  # we need to wait to get our task a bot assigned
          continue
      story_tasks_table[story_id].append(
          RunBenchmarkOnSwarming(apk_path, story_id, bot_id))
    else:
      raise Exception('This should not happen, something went wrong!')
  # CollectResults(task_id, 'test_run_sharding')


if __name__ == '__main__':
  # RunBenchmarkOnSwarming('/usr/local/google/home/wangge/chromium/src/third_party/catapult/experimental/long_term_health/out/52.0.2743.117_arm_ChromeStable.apk', 0)
  # print GetBotId('3fccfa1c9489d710')
  main()