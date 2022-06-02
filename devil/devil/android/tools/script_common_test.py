#!/usr/bin/env python
# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import sys
import tempfile
import unittest

from devil import devil_env
from devil.android import device_errors
from devil.android import device_utils
from devil.android.tools import script_common

with devil_env.SysPath(devil_env.PYMOCK_PATH):
  import mock  # pylint: disable=import-error

with devil_env.SysPath(devil_env.DEPENDENCY_MANAGER_PATH):
  # pylint: disable=wrong-import-order
  from dependency_manager import exceptions


class GetDevicesTest(unittest.TestCase):
  def testNoSpecs(self):
    devices = [
        device_utils.DeviceUtils('123', skip_device_check=True),
        device_utils.DeviceUtils('456', skip_device_check=True),
    ]
    with mock.patch(
        'devil.android.device_utils.DeviceUtils.HealthyDevices',
        return_value=devices):
      self.assertEqual(devices, script_common.GetDevices(None, None))

  @mock.patch('devil.android.sdk.adb_wrapper.AdbWrapper._RunAdbCmd')
  def testWithDevices(self, mock_adb_run):
    mock_adb_run.side_effect = [
        '123 device', '456 device', '456 device', '456 device'
    ]
    devices = [
        device_utils.DeviceUtils('123', skip_device_check=True),
        device_utils.DeviceUtils('456', skip_device_check=True),
    ]
    with mock.patch(
        'devil.android.device_utils.DeviceUtils.HealthyDevices',
        return_value=devices):
      self.assertEqual(
          [device_utils.DeviceUtils('456', skip_device_check=True)],
          script_common.GetDevices(['456'], None))

  def testMissingDevice(self):
    with mock.patch(
        'devil.android.device_utils.DeviceUtils.HealthyDevices',
        return_value=[device_utils.DeviceUtils('123', skip_device_check=True)]):
      with self.assertRaises(device_errors.DeviceUnreachableError):
        script_common.GetDevices(['456'], None)

  def testNoDevices(self):
    with mock.patch(
        'devil.android.device_utils.DeviceUtils.HealthyDevices',
        return_value=[]):
      with self.assertRaises(device_errors.NoDevicesError):
        script_common.GetDevices(None, None)


class InitializeEnvironmentTest(unittest.TestCase):
  def setUp(self):
    # pylint: disable=protected-access
    self.parser = argparse.ArgumentParser()
    script_common.AddEnvironmentArguments(self.parser)
    devil_env.config = devil_env._Environment()

  def testNoAdb(self):
    args = self.parser.parse_args([])
    script_common.InitializeEnvironment(args)
    with self.assertRaises(exceptions.NoPathFoundError):
      devil_env.config.LocalPath('adb')

  def testAdb(self):
    with tempfile.NamedTemporaryFile() as f:
      args = self.parser.parse_args(['--adb-path=%s' % f.name])
      script_common.InitializeEnvironment(args)
      self.assertEqual(f.name, devil_env.config.LocalPath('adb'))

  def testNonExistentAdb(self):
    with tempfile.NamedTemporaryFile() as f:
      args = self.parser.parse_args(['--adb-path=%s' % f.name])
    script_common.InitializeEnvironment(args)
    with self.assertRaises(exceptions.NoPathFoundError):
      devil_env.config.LocalPath('adb')


if __name__ == '__main__':
  sys.exit(unittest.main())
