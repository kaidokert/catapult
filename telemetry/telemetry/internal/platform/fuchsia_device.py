# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A Fuchsia device instance"""

import logging
import os
import sys

from telemetry.core.cros_interface import GetAllCmdOutput
from telemetry.internal.platform import device

CHROMIUM_SOURCE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir,
                  os.pardir, os.pardir, os.pardir))
SDK_ROOT = os.path.join(CHROMIUM_SOURCE_ROOT, 'third_party',
                          'fuchsia-sdk', 'sdk')
_LIST_DEVICES_TIMEOUT_SECS = 3

class FuchsiaDevice(device.Device):
  def __init__(self, target_name, ipv4_address, output_dir,
               system_log_file, port):
    super(FuchsiaDevice, self).__init__(
        name='Fuchsia with host localhost',
        guid='fuchsia:%s' % target_name)
    self._target_name = target_name
    self._ipv4_address = ipv4_address
    self._output_dir = output_dir
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

  @property
  def output_dir(self):
    return self._output_dir
  

def FindAllAvailableDevices(options):
  """Returns a list of available device types."""
  dev_finder_path = os.path.join(SDK_ROOT, 'tools', 'dev_finder')
  command = [dev_finder_path, 'list', '-full',
                 '-timeout', str(_LIST_DEVICES_TIMEOUT_SECS * 1000)]
  device_info, _ = GetAllCmdOutput(command)
  if not device_info:
    logging.info('No Fuchsia device found.')
    return []
  first_device = device_info.split('\n')[0]
  target_name=first_device.split(' ')[1]
  ipv4_address=first_device.split(' ')[0]
  logging.warning('Using Fuchsia device with address %s and name %s'
               % (ipv4_address,target_name))
  return [FuchsiaDevice(target_name=target_name,
                       ipv4_address=ipv4_address,
                       system_log_file=None,
                       output_dir=options.output_dir,
                       port=22)]
