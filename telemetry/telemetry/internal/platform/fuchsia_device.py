# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A Fuchsia device instance"""

import logging
import os
import platform

from telemetry.core import cros_interface
from telemetry.core import util
from telemetry.internal.platform import device

_LIST_DEVICES_TIMEOUT_SECS = 3
_SHA1 = 8897026043691226544

class FuchsiaDevice(device.Device):
  def __init__(self, target_name, host, output_dir,
               system_log_file, port):
    super(FuchsiaDevice, self).__init__(
        name='Fuchsia with host localhost',
        guid='fuchsia:%s' % target_name)
    self._target_name = target_name
    self._output_dir = output_dir
    self._system_log_file = system_log_file
    self._host = host
    self._port = port

  @classmethod
  def GetAllConnectedDevices(cls, blacklist):
    return []

  @property
  def target_name(self):
    return self._target_name

  @property
  def host(self):
    return self._host

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
  # TODO, Add support for Mac.
  if platform.system() != 'Linux' or platform.machine() != 'x86_64':
    logging.warning('Fuchsia in Telemetry only supports Linux x64 hosts.')
    return []

  # Download the Fuchsia sdk if it doesn't exist
  # TODO, figure out how to use the dependency_manager
  SDK_ROOT = os.path.join(util.GetCatapultDir(), os.pardir,
                          'fuchsia-sdk', 'sdk')
  if not os.path.exists(SDK_ROOT):
    gsutil_path = os.path.join(util.GetCatapultDir(), 'third_party', 'gsutil',
                               'gsutil')
    sdk_pkg = 'gs://fuchsia/sdk/core/linux-amd64/' + str(_SHA1)
    tar_file = os.path.join(util.GetCatapultDir(), 'third_party',
                            'fuchsia-sdk.tar')
    if not os.path.isfile(tar_file):
      download_cmd = [gsutil_path, 'cp', sdk_pkg, tar_file]
      cros_interface.RunCmd(download_cmd)

    SDK_ROOT = os.path.join(util.GetCatapultDir(), 'third_party',
                            'fuchsia-sdk', 'sdk')
    if not os.path.exists(SDK_ROOT):
      os.makedirs(SDK_ROOT)
      decompress_cmd = ['tar', '-C', SDK_ROOT, '-xvf', tar_file]
      decompress_cmd.extend(['tools/dev_finder', 'tools/symbolize'])
      cros_interface.RunCmd(decompress_cmd)

  dev_finder_path = os.path.join(SDK_ROOT, 'tools', 'dev_finder')
  finder_cmd = [dev_finder_path, 'list', '-full',
                '-timeout', str(_LIST_DEVICES_TIMEOUT_SECS * 1000)]
  device_info, _ = cros_interface.GetAllCmdOutput(finder_cmd)
  if not device_info:
    logging.info('No Fuchsia device found.')
    return []
  first_device = device_info.split('\n')[0]
  target_name = first_device.split(' ')[1]
  host = first_device.split(' ')[0]
  logging.warning('Using Fuchsia device with address %s and name %s'
                  % (host, target_name))
  return [FuchsiaDevice(target_name=target_name,
                        host=host,
                        system_log_file=None,
                        output_dir=options.output_dir,
                        port=22)]
