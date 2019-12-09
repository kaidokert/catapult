# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from telemetry.core import fuchsia_interface
from telemetry.internal.browser import browser_options
from telemetry.internal.platform import fuchsia_device
import mock


class FuchsiaDeviceTest(unittest.TestCase):
  #def testDecompressFuchsiaSDK(self):

  def testFindFuchsiadevice(self):
    is_emulator = True
    self.assertEquals(fuchsia_device._FindFuchsiaDevice(is_emulator), None)
    is_emulator = False
    with mock.patch('telemetry.util.cmd_util.GetAllCmdOutput',
                    return_value=['device list', None]):
      self.assertEquals(fuchsia_device._FindFuchsiaDevice(is_emulator),
                        'device list')

  def testFindAllAvailableDevicesFails(self):
    options = browser_options.BrowserFinderOptions('not_fuchsia_browser')
    self.assertEquals(fuchsia_device.FindAllAvailableDevices(options), [])
    options = browser_options.BrowserFinderOptions(
        fuchsia_interface.FUCHSIA_BROWSERS[0])
    with mock.patch('platform.system', return_value='not_Linux'):
      self.assertEquals(fuchsia_device.FindAllAvailableDevices(options), [])
    mock.patch('platform.system', return_value='Linux')
    with mock.patch('platform.machine', return_value='x86_32'):
      self.assertEquals(fuchsia_device.FindAllAvailableDevices(options), [])

  def testFindAllAvailableDevice(self):
    def side_effect(path):
      if path == fuchsia_device._SDK_ROOT_IN_CHROMIUM:
        return True
      if path == fuchsia_device._SDK_ROOT_IN_CATAPULT:
        return False
      raise Exception('Invalid path to Fuchsia SDK.')

    options = browser_options.BrowserFinderOptions(
        fuchsia_interface.FUCHSIA_BROWSERS[0])
    mock.patch('platform.system', return_value='Linux')
    mock.patch('platform.machine', return_value='x86_64')
    with mock.patch('os.path.exists', return_value=True):
      with mock.patch('telemetry.internal.platform.'
                      'fuchsia_device._FindFuchsiaDevice',
                      return_value=None) as find_mock:
        decompress_mock = mock.patch('telemetry.internal.platform.'
                                     'fuchsia_device._DecompressFuchsiaSDK')
        self.assertEquals(fuchsia_device.FindAllAvailableDevices(options),
                          [])
        self.assertEquals(decompress_mock.call_count, 0)
