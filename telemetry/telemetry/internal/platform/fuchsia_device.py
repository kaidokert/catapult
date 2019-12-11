# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A Fuchsia device instance"""

import logging
import os
import platform
import tarfile

from telemetry.core import fuchsia_interface
from telemetry.core import util
from telemetry.internal.platform import device
from telemetry.util import cmd_util

_LIST_DEVICES_TIMEOUT_MILLISECS = 5000
_SDK_SHA1 = '8894838554076535504'
_SDK_ROOT_IN_CATAPULT = os.path.join(util.GetCatapultDir(), 'third_party',
                                     'fuchsia-sdk', 'sdk')
_SDK_ROOT_IN_CHROMIUM = os.path.join(util.GetCatapultDir(), '..',
                                     'fuchsia-sdk', 'sdk')
_SDK_TOOLS = ['tools/dev_finder', 'tools/symbolize']


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


def _GetFuchsiaSDK(tar_file, dest=_SDK_ROOT_IN_CATAPULT):
  if not os.path.isdir(dest):
    os.makedirs(dest)
  gsutil_path = os.path.join(util.GetCatapultDir(), 'third_party', 'gsutil',
                             'gsutil')
  sdk_pkg = 'gs://fuchsia/sdk/core/linux-amd64/' + _SDK_SHA1
  download_cmd = [gsutil_path, 'cp', sdk_pkg, tar_file]
  cmd_util.RunCmd(download_cmd)

  with tarfile.open(tar_file, 'r') as tar:
    for f in _SDK_TOOLS:
      tar.extract(f, dest)
  os.remove(tar_file)


def _FindFuchsiaDevice(sdk_root, is_emulator):
  dev_finder_path = os.path.join(sdk_root, 'tools', 'dev_finder')
  if is_emulator:
    logging.warning('Fuchsia emulators not supported at this time.')
    return None
  finder_cmd = [dev_finder_path, 'list', '-full',
                '-timeout', str(_LIST_DEVICES_TIMEOUT_MILLISECS)]
  device_list, _ = cmd_util.GetAllCmdOutput(finder_cmd)
  if not device_list:
    logging.warning('No Fuchsia device found.')
  return device_list


def _DownloadFuchsiaSDKIfNecessary():
  """Downloads the Fuchsia SDK if not found in Chromium and Catapult repo

  Returns:
    The path to the Fuchsia SDK directory
  """
  if not os.path.exists(_SDK_ROOT_IN_CHROMIUM):
    if not os.path.exists(_SDK_ROOT_IN_CATAPULT):
      tar_file = os.path.join(_SDK_ROOT_IN_CATAPULT,
                              'fuchsia-sdk-%s.tar' % _SDK_SHA1)
      _GetFuchsiaSDK(tar_file)
    return _SDK_ROOT_IN_CATAPULT
  return _SDK_ROOT_IN_CHROMIUM


def FindAllAvailableDevices(options):
  """Returns a list of available device types."""

  # Will not find Fuchsia devices if Fuchsia browser is not specified
  # This means that unless specifying browser=web-engine-shell, the user
  # will not see web-engine-shell as an available browser.
  if options.browser_type not in fuchsia_interface.FUCHSIA_BROWSERS:
    return []

  if platform.system() != 'Linux' or platform.machine() != 'x86_64':
    logging.warning('Fuchsia in Telemetry only supports Linux x64 hosts.')
    return []

  # Download the Fuchsia sdk if it doesn't exist
  # TODO(https://crbug.com/1031763): Figure out how to use the dependency
  # manager
  sdk_root = _DownloadFuchsiaSDKIfNecessary()

  device_list = _FindFuchsiaDevice(sdk_root, False)
  if not device_list:
    return []
  # Expected output will look something like
  # 'host0 target0\nhost1 target1\nhost2 target2'
  first_device = device_list.splitlines()[0]
  host, target_name = first_device.split(' ')

  logging.info('Using Fuchsia device with address %s and name %s'
               % (host, target_name))
  return [FuchsiaDevice(target_name=target_name,
                        host=host,
                        system_log_file=None,
                        output_dir=options.fuchsia_output_dir,
                        port=22)]
