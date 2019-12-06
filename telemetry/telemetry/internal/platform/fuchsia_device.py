# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A Fuchsia device instance"""

import logging
import os
import platform

from telemetry.core import fuchsia_interface
from telemetry.core import util
from telemetry.internal.platform import device

_LIST_DEVICES_TIMEOUT_SECS = 5
_SHA1 = 8894838554076535504
_SDK_ROOT_IN_CATAPULT = os.path.join(util.GetCatapultDir(), 'third_party',
                                     'fuchsia-sdk', 'sdk')

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
  def output_dir(self):
    return self._output_dir

  @property
  def system_log_file(self):
    return self._system_log_file

  @property
  def port(self):
    return self._port


def _DownloadFuchsiaSDK(dest):
  gsutil_path = os.path.join(util.GetCatapultDir(), 'third_party', 'gsutil',
                             'gsutil')
  sdk_pkg = 'gs://fuchsia/sdk/core/linux-amd64/' + str(_SHA1)
  download_cmd = [gsutil_path, 'cp', sdk_pkg, dest]
  fuchsia_interface.RunCmd(download_cmd)

def _DecompressFuchsiaSDK(tar_file):
  decompress_cmd = ['tar', '-C', _SDK_ROOT_IN_CATAPULT, '-xvf', tar_file]
  decompress_cmd.extend(['tools/dev_finder', 'tools/symbolize'])
  fuchsia_interface.RunCmd(decompress_cmd)

def _FindFuchsiaDevice(is_emulator):
  dev_finder_path = os.path.join(_SDK_ROOT_IN_CATAPULT, 'tools', 'dev_finder')
  if is_emulator:
    logging.warning('Fuchsia emulators not supported at this time.')
    return None
  finder_cmd = [dev_finder_path, 'list', '-full',
                '-timeout', str(_LIST_DEVICES_TIMEOUT_SECS * 1000)]
  device_list, _ = fuchsia_interface.GetAllCmdOutput(finder_cmd)
  if not device_list:
    logging.warning('No Fuchsia device found.')
  return device_list

def FindAllAvailableDevices(options):
  """Returns a list of available device types."""

  # Will not find Fuchsia devices if Fuchsia browser is not specified
  if options.browser_type != 'web-engine-shell':
    return []

  if platform.system() != 'Linux' or platform.machine() != 'x86_64':
    logging.warning('Fuchsia in Telemetry only supports Linux x64 hosts.')
    return []

  # Download the Fuchsia sdk if it doesn't exist
  # TODO, figure out how to use the dependency_manager
  SDK_ROOT_IN_CHROMIUM = os.path.join(util.GetCatapultDir(), os.pardir,
                                      'fuchsia-sdk', 'sdk')
  if not os.path.exists(SDK_ROOT_IN_CHROMIUM):
    # Set SDK_ROOT to inside Catapult

    tar_file = os.path.join(util.GetCatapultDir(), 'third_party',
                            'fuchsia-sdk-%s.tar' % _SHA1)
    if not os.path.exists(_SDK_ROOT_IN_CATAPULT):
      os.makedirs(_SDK_ROOT_IN_CATAPULT)
      if not os.path.isfile(tar_file):
        _DownloadFuchsiaSDK(tar_file)
      _DecompressFuchsiaSDK(tar_file)

  device_list = _FindFuchsiaDevice(False)
  if not device_list:
    return []
  first_device = device_list.split('\n')[0]
  target_name = first_device.split(' ')[1]
  host = first_device.split(' ')[0]

  logging.info('Using Fuchsia device with address %s and name %s'
               % (host, target_name))
  return [FuchsiaDevice(target_name=target_name,
                        host=host,
                        system_log_file=None,
                        output_dir=options.fuchsia_output_dir,
                        port=22)]
