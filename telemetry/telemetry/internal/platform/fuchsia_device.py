# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A Fuchsia device instance"""

import logging
import sys
logging.warning(sys.path)

from fuchsia.sdk_helper import sdk_helper
from telemetry.internal.platform import device

class FuchsiaDevice(device.Device):
  def __init__(self, target_name, ipv4_address, system_log_file=None, port=22):
    super(FuchsiaDevice, self).__init__(
        name='Fuchsia with host localhost',
        guid='fuchsia:%s' % target_name)
    self._target_name = target_name
    self._ipv4_address = ipv4_address
    self._system_log_file = system_log_file
    self._port = port

  @classmethod
  def GetAllConnectedDevices(cls, blacklist):
    return []

  @property
  def target_name(self):
    return self._target_name

  @property
  def ssh_port(self):
    return self._ssh_port

  @property
  def system_log_file(self):
    return self._system_log_file

  @property
  def port(self):
    return self._port

def FindAllAvailableDevices(options):
  """Returns a list of available device types."""
  proc = sdk_helper.findDevices()
  device_info = proc.communicate()[0].split('\n')[0]
  logging.warning(device_info.split(' ')[0])
  return [FuchsiaDevice(target_name=device_info.split(' ')[1],
                       ipv4_address=device_info.split(' ')[0],
                       system_log_file=sys.stdout,
                       port=22)]
