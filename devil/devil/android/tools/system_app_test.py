#!/usr/bin/env python
# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
import unittest

if __name__ == '__main__':
  sys.path.append(os.path.abspath(
      os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from devil import devil_env
from devil.android import device_utils
from devil.android.sdk import adb_wrapper
from devil.android.sdk import version_codes
from devil.android.tools import system_app

with devil_env.SysPath(devil_env.PYMOCK_PATH):
  import mock


_PACKAGE_NAME = 'com.android'
_PACKAGE_PATH = '/path/to/com.android.apk'
_DUMPSYS_COMMAND = ['dumpsys', 'package', _PACKAGE_NAME]
_DUMPSYS_OUTPUT_WITH_PATH = ['some path: /bad/path',
                             '  path: ' + _PACKAGE_PATH,
                             '  path: not really a path']
_DUMPSYS_OUTPUT_WITHOUT_PATH = ['some path: /bad/path',
                                '  path: not really a path']

class SystemAppTest(unittest.TestCase):

  def testDoubleEnableModification(self):
    """Ensures that system app modification logic isn't repeated.

    If EnableSystemAppModification uses are nested, inner calls should
    not need to perform any of the expensive modification logic.
    """
    # pylint: disable=no-self-use,protected-access
    mock_device = mock.Mock(spec=device_utils.DeviceUtils)
    mock_device.adb = mock.Mock(spec=adb_wrapper.AdbWrapper)
    type(mock_device).build_version_sdk = mock.PropertyMock(
        return_value=version_codes.LOLLIPOP)

    system_props = {}

    def dict_setprop(prop_name, value):
      system_props[prop_name] = value

    def dict_getprop(prop_name):
      return system_props.get(prop_name, '')

    mock_device.SetProp.side_effect = dict_setprop
    mock_device.GetProp.side_effect = dict_getprop

    with system_app.EnableSystemAppModification(mock_device):
      mock_device.EnableRoot.assert_called_once_with()
      mock_device.GetProp.assert_called_once_with(
          system_app._ENABLE_MODIFICATION_PROP)
      mock_device.SetProp.assert_called_once_with(
          system_app._ENABLE_MODIFICATION_PROP, '1')
      mock_device.reset_mock()

      with system_app.EnableSystemAppModification(mock_device):
        self.assertFalse(mock_device.EnableRoot.mock_calls)  # assert not called
        mock_device.GetProp.assert_called_once_with(
            system_app._ENABLE_MODIFICATION_PROP)
        self.assertFalse(mock_device.SetProp.mock_calls)  # assert not called
        mock_device.reset_mock()

    mock_device.SetProp.assert_called_once_with(
        system_app._ENABLE_MODIFICATION_PROP, '0')

  def test_GetApplicationPaths_pmPathAndDumpsys(self):
    """Path found in both GetApplicationPaths and dumpsys package outputs."""
    # pylint: disable=protected-access
    mock_device = mock.Mock(spec=device_utils.DeviceUtils)
    mock_device.configure_mock(build_version_sdk=24)
    mock_device.GetApplicationPaths.configure_mock(
        return_value=[_PACKAGE_PATH]
    )
    mock_device.RunShellCommand.configure_mock(
        return_value=_DUMPSYS_OUTPUT_WITH_PATH
    )

    paths = system_app._GetApplicationPaths(mock_device, _PACKAGE_NAME)

    self.assertEquals([_PACKAGE_PATH], paths)
    mock_device.GetApplicationPaths.assert_called_once_with(_PACKAGE_NAME)
    mock_device.RunShellCommand.assert_called_once_with(_DUMPSYS_COMMAND,
                                                        large_output=True)

  def test_GetApplicationPaths_DumpsysOnly(self):
    """Path only found in dumpsys package output."""
    # pylint: disable=protected-access
    mock_device = mock.Mock(spec=device_utils.DeviceUtils)
    mock_device.configure_mock(build_version_sdk=24)
    mock_device.GetApplicationPaths.configure_mock(return_value=[])
    mock_device.RunShellCommand.configure_mock(
        return_value=_DUMPSYS_OUTPUT_WITH_PATH
    )

    paths = system_app._GetApplicationPaths(mock_device, _PACKAGE_NAME)

    self.assertEquals([_PACKAGE_PATH], paths)
    mock_device.GetApplicationPaths.assert_called_once_with(_PACKAGE_NAME)
    mock_device.RunShellCommand.assert_called_once_with(_DUMPSYS_COMMAND,
                                                        large_output=True)

  def test_GetApplicationPaths_pmPathOnly(self):
    """Path only found in GetApplicationPaths output."""
    # pylint: disable=protected-access
    mock_device = mock.Mock(spec=device_utils.DeviceUtils)
    mock_device.configure_mock(build_version_sdk=24)
    mock_device.GetApplicationPaths.configure_mock(
        return_value=[_PACKAGE_PATH]
    )
    mock_device.RunShellCommand.configure_mock(
        return_value=_DUMPSYS_OUTPUT_WITHOUT_PATH
    )

    paths = system_app._GetApplicationPaths(mock_device, _PACKAGE_NAME)

    self.assertEquals([_PACKAGE_PATH], paths)
    mock_device.GetApplicationPaths.assert_called_once_with(_PACKAGE_NAME)
    mock_device.RunShellCommand.assert_called_once_with(_DUMPSYS_COMMAND,
                                                        large_output=True)

  def test_GetApplicationPaths_preN(self):
    """Before N, should only use GetApplicationPaths."""
    # pylint: disable=protected-access
    mock_device = mock.Mock(spec=device_utils.DeviceUtils)
    mock_device.configure_mock(build_version_sdk=23)
    mock_device.GetApplicationPaths.configure_mock(
        return_value=[_PACKAGE_PATH]
    )

    paths = system_app._GetApplicationPaths(mock_device, _PACKAGE_NAME)

    self.assertEquals([_PACKAGE_PATH], paths)
    mock_device.GetApplicationPaths.assert_called_once_with(_PACKAGE_NAME)
    mock_device.RunShellCommand.assert_not_called()


if __name__ == '__main__':
  unittest.main()
