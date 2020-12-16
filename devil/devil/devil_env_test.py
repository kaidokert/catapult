#!/usr/bin/env python
# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# pylint: disable=protected-access

import logging
import os
import sys
import unittest

from devil import devil_env

with devil_env.SysPaths(devil_env.PYMOCK_AND_DEPS_PATHS):
  import mock  # pylint: disable=import-error


class DevilEnvTest(unittest.TestCase):
  def testSysPathPop(self):
    # Test popping at the end of the list.
    path_to_add = os.path.join(devil_env.CATAPULT_ROOT_PATH, 'notarealdir')
    sys_path_before = list(sys.path)
    with devil_env.SysPath(path_to_add):
      sys_path_during = list(sys.path)
    sys_path_after = list(sys.path)
    self.assertEqual(sys_path_before, sys_path_after)
    self.assertEqual(sys_path_before + [path_to_add], sys_path_during)

  def testSysPathRemove(self):
    # Test removing mid-list.
    path_to_add = os.path.join(devil_env.CATAPULT_ROOT_PATH, 'notarealdir')
    additional_path = os.path.join(devil_env.CATAPULT_ROOT_PATH, 'fakedir')

    try:
      sys_path_before = list(sys.path)
      with devil_env.SysPath(path_to_add):
        sys_path_during = list(sys.path)
        sys.path.append(additional_path)
      sys_path_after = list(sys.path)
      self.assertEqual(sys_path_before + [additional_path], sys_path_after)
      self.assertEqual(sys_path_before + [path_to_add], sys_path_during)
    finally:
      if additional_path in sys.path:
        sys.path.remove(additional_path)

  def testSysPathsPop(self):
    # Test popping at the end of the list.
    paths_to_add = [
        os.path.join(devil_env.CATAPULT_ROOT_PATH, 'notarealdir'),
        os.path.join(devil_env.CATAPULT_ROOT_PATH, 'fakedir'),
    ]
    sys_path_before = list(sys.path)
    with devil_env.SysPaths(paths_to_add):
      sys_path_during = list(sys.path)
    sys_path_after = list(sys.path)
    self.assertEqual(sys_path_before, sys_path_after)
    self.assertEqual(sys_path_before + paths_to_add, sys_path_during)

  def testSysPathsRemove(self):
    # Test removing mid-list.
    paths_to_add = [
        os.path.join(devil_env.CATAPULT_ROOT_PATH, 'notarealdir'),
        os.path.join(devil_env.CATAPULT_ROOT_PATH, 'fakedir'),
    ]
    additional_path = os.path.join(devil_env.CATAPULT_ROOT_PATH, 'anotherfake')

    try:
      sys_path_before = list(sys.path)
      with devil_env.SysPaths(paths_to_add):
        sys_path_during = list(sys.path)
        sys.path.append(additional_path)
      sys_path_after = list(sys.path)
      self.assertEqual(sys_path_before + [additional_path], sys_path_after)
      self.assertEqual(sys_path_before + paths_to_add, sys_path_during)
    finally:
      if additional_path in sys.path:
        sys.path.remove(additional_path)

  def testGetEnvironmentVariableConfig_configType(self):
    with mock.patch('os.environ.get',
                    mock.Mock(side_effect=lambda _env_var: None)):
      env_config = devil_env._GetEnvironmentVariableConfig()
    self.assertEquals('BaseConfig', env_config.get('config_type'))

  def testGetEnvironmentVariableConfig_noEnv(self):
    with mock.patch('os.environ.get',
                    mock.Mock(side_effect=lambda _env_var: None)):
      env_config = devil_env._GetEnvironmentVariableConfig()
    self.assertEquals({}, env_config.get('dependencies'))

  def testGetEnvironmentVariableConfig_adbPath(self):
    def mock_environment(env_var):
      return '/my/fake/adb/path' if env_var == 'ADB_PATH' else None

    with mock.patch('os.environ.get', mock.Mock(side_effect=mock_environment)):
      env_config = devil_env._GetEnvironmentVariableConfig()
    self.assertEquals({
        'adb': {
            'file_info': {
                'linux2_x86_64': {
                    'local_paths': ['/my/fake/adb/path'],
                },
            },
        },
    }, env_config.get('dependencies'))


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.DEBUG)
  unittest.main(verbosity=2)
