# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from telemetry.core import fuchsia_interface
from telemetry.internal.browser import browser_options
from telemetry.internal.platform import fuchsia_device
import mock

_FUCHSIA_DEVICE_IMPORT_PATH = 'telemetry.internal.platform.fuchsia_device'


class FuchsiaDeviceTest(unittest.TestCase):

  def testFindFuchsiadevice(self):
    is_emulator = True
    self.assertEquals(fuchsia_device._FindFuchsiaDevice(is_emulator), None)
    is_emulator = False
    with mock.patch('telemetry.util.cmd_util.GetAllCmdOutput',
                    return_value=['device list', None]):
      self.assertEquals(fuchsia_device._FindFuchsiaDevice(is_emulator),
                        'device list')

  def testFindAllAvailableDevicesFailsNonFuchsiaBrowser(self):
    options = browser_options.BrowserFinderOptions('not_fuchsia_browser')
    self.assertEquals(fuchsia_device.FindAllAvailableDevices(options), [])

  def testFindAllAvailableDevicesFailsNonLinuxHost(self):
    options = browser_options.BrowserFinderOptions(
        fuchsia_interface.FUCHSIA_BROWSERS[0])
    with mock.patch('platform.system', return_value='not_Linux'):
      self.assertEquals(fuchsia_device.FindAllAvailableDevices(options), [])

  def testFindAllAvailableDevicesFailsNonx64(self):
    options = browser_options.BrowserFinderOptions(
        fuchsia_interface.FUCHSIA_BROWSERS[0])
    with mock.patch('platform.system', return_value='Linux'):
      with mock.patch('platform.machine', return_value='i386'):
        self.assertEquals(fuchsia_device.FindAllAvailableDevices(options), [])


class FuchsiaSDKUsageTest(unittest.TestCase):
  def setUp(self):
    mock.patch('platform.system', return_value='Linux').start()
    mock.patch('platform.machine', return_value='x86_64').start()
    self._options = browser_options.BrowserFinderOptions(
        fuchsia_interface.FUCHSIA_BROWSERS[0])
    self._options.fuchsia_output_dir = 'test/'

  def tearDown(self):
    mock.patch.stopall()

  def testSkipDownloadSDKIfExists(self):
    def side_effect(path):
      if path == fuchsia_device._SDK_ROOT_IN_CHROMIUM:
        return True
      if path == fuchsia_device._SDK_ROOT_IN_CATAPULT:
        return False
    with mock.patch('os.path.exists', return_value=True) as path_mock:
      with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH +
                      '._GetFuchsiaSDK') as get_mock:
        with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH + '._FindFuchsiaDevice',
                        return_value=None) as find_mock:
          self.assertEquals(fuchsia_device.FindAllAvailableDevices(
              self._options), [])
          self.assertEquals(get_mock.call_count, 0)
          self.assertEquals(find_mock.call_count, 1)

          path_mock.side_effect = side_effect
          self.assertEquals(fuchsia_device.FindAllAvailableDevices(
              self._options), [])
          self.assertEquals(get_mock.call_count, 0)
          self.assertEquals(find_mock.call_count, 2)

  def testFoundZeroFuchsiaDevice(self):
    with mock.patch('os.path.exists', return_value=True):
      with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH + '._FindFuchsiaDevice',
                      return_value=None):
        self.assertEquals(fuchsia_device.FindAllAvailableDevices(
            self._options), [])

  def testFoundOneFuchsiaDevice(self):
    with mock.patch('os.path.exists', return_value=True):
      with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH + '._FindFuchsiaDevice',
                      return_value='host0 target0'):
        found_devices = fuchsia_device.FindAllAvailableDevices(self._options)
        self.assertEquals(len(found_devices), 1)
        device = found_devices[0]
        self.assertEquals(device.host, 'host0')
        self.assertEquals(device.target_name, 'target0')

  def testFoundMultipleFuchsiaDevices(self):
    with mock.patch('os.path.exists', return_value=True):
      with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH + '._FindFuchsiaDevice',
                      return_value='host0 target0\nhost1 target1'):
        found_devices = fuchsia_device.FindAllAvailableDevices(self._options)
        self.assertEquals(len(found_devices), 1)
        device = found_devices[0]
        self.assertEquals(device.host, 'host0')
        self.assertEquals(device.target_name, 'target0')
