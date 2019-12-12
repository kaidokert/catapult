# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import os
import shutil
import tarfile
import tempfile
import unittest

from telemetry.core import fuchsia_interface
from telemetry.internal.browser import browser_options
from telemetry.internal.platform import fuchsia_device
import mock

_FUCHSIA_DEVICE_IMPORT_PATH = 'telemetry.internal.platform.fuchsia_device'


class FuchsiaDeviceTest(unittest.TestCase):

  def testFindFuchsiaDeviceFailsEmulator(self):
    is_emulator = True
    self.assertEquals(fuchsia_device._FindFuchsiaDevice('', is_emulator), None)

  def testFindFuchsiaDevice(self):
    is_emulator = False
    with mock.patch('telemetry.util.cmd_util.GetAllCmdOutput',
                    return_value=['device list', None]):
      self.assertEquals(fuchsia_device._FindFuchsiaDevice('', is_emulator),
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

  def testDownloadSDKIfNotExists(self):
    with mock.patch('os.path.exists', return_value=False):
      with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH +
                      '._GetFuchsiaSDK') as get_mock:
        with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH + '._FindFuchsiaDevice',
                        return_value=None) as find_mock:
          self.assertEquals(fuchsia_device.FindAllAvailableDevices(
              self._options), [])
          self.assertEquals(get_mock.call_count, 1)
          self.assertEquals(find_mock.call_count, 1)

  def testDecompressSDK(self):
    def side_effect(cmd):
      tar_file = cmd[-1]
      with tarfile.open(tar_file, 'w') as tar:
        temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(temp_dir, 'tools'))
        for f in fuchsia_device._SDK_TOOLS:
          with open(os.path.join(temp_dir, f), 'a+') as temp_file:
            tar.add(temp_file.name, arcname=f)
        shutil.rmtree(temp_dir)

    temp_dir = tempfile.mkdtemp()
    test_tar = os.path.join(temp_dir, 'test.tar')
    with mock.patch('telemetry.util.cmd_util.RunCmd') as cmd_mock:
      cmd_mock.side_effect = side_effect
      fuchsia_device._GetFuchsiaSDK(test_tar, temp_dir)
      for f in fuchsia_device._SDK_TOOLS:
        self.assertTrue(os.path.isfile(os.path.join(temp_dir, f)))
    self.assertFalse(os.path.isfile(os.path.join(
        temp_dir, test_tar)))
    shutil.rmtree(temp_dir)

  def testSkipDownloadSDKIfExistsInChromium(self):
    with mock.patch('os.path.exists', return_value=True):
      with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH +
                      '._GetFuchsiaSDK') as get_mock:
        with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH + '._FindFuchsiaDevice',
                        return_value=None) as find_mock:
          self.assertEquals(fuchsia_device.FindAllAvailableDevices(
              self._options), [])
          self.assertEquals(get_mock.call_count, 0)
          self.assertEquals(find_mock.call_count, 1)

  def testSkipDownloadSDKIfExistsInCatapult(self):
    def side_effect(path):
      if path == fuchsia_device._SDK_ROOT_IN_CHROMIUM:
        return True
      if path == fuchsia_device._SDK_ROOT_IN_CATAPULT:
        return False
      raise RuntimeError('Invalid path to Fuchsia SDK')

    with mock.patch('os.path.exists') as path_mock:
      with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH +
                      '._GetFuchsiaSDK') as get_mock:
        with mock.patch(_FUCHSIA_DEVICE_IMPORT_PATH + '._FindFuchsiaDevice',
                        return_value=None) as find_mock:
          path_mock.side_effect = side_effect
          self.assertEquals(fuchsia_device.FindAllAvailableDevices(
              self._options), [])
          self.assertEquals(get_mock.call_count, 0)
          self.assertEquals(find_mock.call_count, 1)

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
