# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import unittest

from telemetry.internal.platform import fuchsia_device


class FuchsiaDeviceTest(unittest.TestCase):
  def testConstruction(self):
    self.assertEquals(fuchsia_device.FuchsiaDevice.GetAllConnectedDevices(None),
                      [])
    device = fuchsia_device.FuchsiaDevice('target', '1.0.0.0', 'out/Fuchsia',
                                          'system_log', 22)
    self.assertEquals(device.target_name, 'target')
    self.assertEquals(device.host, '1.0.0.0')
    self.assertEquals(device.output_dir, 'out/Fuchsia')
    self.assertEquals(device.system_log_file, 'system_log')
    self.assertEquals(device.port, 22)
