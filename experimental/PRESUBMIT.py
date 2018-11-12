# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


def _RunUnitTests(input_api, output_api):
  test_env = dict(input_api.environ)
  test_env.update({'PYTHONDONTWRITEBYTECODE': '1'})

  message_type = (output_api.PresubmitError if input_api.is_committing
                  else output_api.PresubmitPromptWarning)

  return input_api.RunTests([
      input_api.Command(
          name='soundwave/bin/run_tests',
          cmd=[input_api.os_path.join(
              input_api.PresubmitLocalPath(), 'soundwave', 'bin', 'run_tests')],
          kwargs={'env': test_env},
          message=message_type)])


def CheckChangeOnUpload(input_api, output_api):
  return _CommonChecks(input_api, output_api)


def CheckChangeOnCommit(input_api, output_api):
  return _CommonChecks(input_api, output_api)


def _CommonChecks(input_api, output_api):
  results = []
  results += input_api.RunTests(input_api.canned_checks.GetPylint(
      input_api, output_api, extra_paths_list=_GetPathsToPrepend(input_api),
      pylintrc='../pylintrc'))
  results += _RunUnitTests(input_api, output_api)
  return results


def _GetPathsToPrepend(input_api):
  project_dir = input_api.PresubmitLocalPath()
  catapult_dir = input_api.os_path.join(project_dir, '..')
  return [
      project_dir,

      input_api.os_path.join(catapult_dir, 'third_party', 'mock'),
      input_api.os_path.join(catapult_dir, 'tracing'),
  ]
