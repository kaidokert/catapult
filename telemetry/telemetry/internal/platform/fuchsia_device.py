# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A Fuchsia device instance"""

import logging
import os
import platform
import subprocess
import tarfile

from telemetry.core import fuchsia_interface
from telemetry.core import util
from telemetry.internal.platform import device
from telemetry.util import cmd_util

_LIST_DEVICES_TIMEOUT_SECS = 5
_SDK_SHA1 = '8894838554076535504'
_SDK_ROOT_IN_CATAPULT = os.path.join(util.GetCatapultDir(), 'third_party',
                                     'fuchsia-sdk', 'sdk')
_SDK_ROOT_IN_CHROMIUM = os.path.join(util.GetCatapultDir(), '..',
                                     'fuchsia-sdk', 'sdk')
_SDK_TOOLS = [
    os.path.join('tools', 'x64', 'ffx'),
    os.path.join('tools', 'x64', 'symbolize')
]


# TODO(omerlevran): Remove before submitting.
os.environ["FUCHSIA_ANALYTICS_DISABLED"] = '1'

logging.warning('*******************Getting ENV VARIABLES FOR FFX*********************************')
for x in ['SWARMING_BOT_ID', 'CODEBUILD_BUILD_ID', 'CIRCLECI']:
  if os.getenv(x) is not None:
    logging.warning('%s' % str(os.getenv(x)))
    logging.warning('%s' % str(x))
logging.warning('*******************Done getting ENV VARIABLES FOR FFX*********************************')
class FuchsiaDevice(device.Device):

  def __init__(self, target_name, host, ssh_config,
               system_log_file, port, managed_repo):
    super(FuchsiaDevice, self).__init__(
        name='Fuchsia with host: %s' % host,
        guid='fuchsia:%s' % target_name)
    self._target_name = target_name
    self._ssh_config = ssh_config
    self._system_log_file = system_log_file
    self._host = host
    self._port = port
    self._managed_repo = managed_repo

  @classmethod
  def GetAllConnectedDevices(cls, denylist):
    return []

  @property
  def managed_repo(self):
    return self._managed_repo

  @property
  def target_name(self):
    return self._target_name

  @property
  def host(self):
    return self._host

  @property
  def ssh_config(self):
    return self._ssh_config

  @property
  def system_log_file(self):
    return self._system_log_file

  @property
  def port(self):
    return self._port


def _DownloadFuchsiaSDK(tar_file, dest=_SDK_ROOT_IN_CATAPULT):
  if not os.path.isdir(dest):
    os.makedirs(dest)
  gsutil_path = os.path.join(util.GetCatapultDir(), 'third_party', 'gsutil',
                             'gsutil')
  sdk_pkg = 'gs://fuchsia/sdk/core/linux-amd64/' + _SDK_SHA1
  download_cmd = [gsutil_path, 'cp', sdk_pkg, tar_file]
  subprocess.check_output(download_cmd, stderr=subprocess.STDOUT)

  with tarfile.open(tar_file, 'r') as tar:
    for f in _SDK_TOOLS:
      # tarfile only accepts POSIX paths.
      tar.extract(f.replace(os.path.sep, '/'), dest)
  os.remove(tar_file)


def _FindFuchsiaDevice(sdk_root, is_emulator):
  ffx_path = os.path.join(sdk_root, 'tools', 'x64', 'ffx')
  if is_emulator:
    logging.warning('Fuchsia emulators not supported at this time.')
    return None
  ffx_cmd = [ffx_path, '-T',
             str(_LIST_DEVICES_TIMEOUT_SECS), 'target', 'list', '--format', 's']
  device_list, _ = cmd_util.GetAllCmdOutput(ffx_cmd)
  if not device_list:
    logging.warning('No Fuchsia device found. Ensure your device is set up '
                    'and can be connected to.')
  return device_list


def _DownloadFuchsiaSDKIfNecessary():
  """Downloads the Fuchsia SDK if not found in Chromium and Catapult repo.

  Returns:
    The path to the Fuchsia SDK directory
  """
  if os.path.exists(_SDK_ROOT_IN_CHROMIUM):
    return _SDK_ROOT_IN_CHROMIUM
  if not os.path.exists(_SDK_ROOT_IN_CATAPULT):
    tar_file = os.path.join(_SDK_ROOT_IN_CATAPULT,
                            'fuchsia-sdk-%s.tar' % _SDK_SHA1)
    _DownloadFuchsiaSDK(tar_file)
  return _SDK_ROOT_IN_CATAPULT


def FindAllAvailableDevices(options):
  """Returns a list of available device types."""

  # Will not find Fuchsia devices if Fuchsia browser is not specified.
  # This means that unless specifying browser=web-engine-shell, the user
  # will not see web-engine-shell as an available browser.
  if options.browser_type not in fuchsia_interface.FUCHSIA_BROWSERS:
    return []

  if platform.system() != 'Linux' or platform.machine() != 'x86_64':
    logging.warning('Fuchsia in Telemetry only supports Linux x64 hosts.')
    return []

  # If the ssh port of the device has been forwarded to a port on the host,
  # return that device directly.
  if options.fuchsia_ssh_port:
    return [FuchsiaDevice(target_name='local_device',
                          host='localhost',
                          system_log_file=options.fuchsia_system_log_file,
                          ssh_config=options.fuchsia_ssh_config,
                          port=options.fuchsia_ssh_port,
                          managed_repo=options.fuchsia_repo)]

  # If the IP address of the device is specified, use that directly.
  elif options.fuchsia_device_address:
    return [FuchsiaDevice(target_name='device_target',
                          host=options.fuchsia_device_address,
                          system_log_file=options.fuchsia_system_log_file,
                          ssh_config=options.fuchsia_ssh_config,
                          port=options.fuchsia_ssh_port,
                          managed_repo=options.fuchsia_repo)]

  # Download the Fuchsia SDK if it doesn't exist.
  # TODO(https://crbug.com/1031763): Figure out how to use the dependency
  # manager.
  sdk_root = _DownloadFuchsiaSDKIfNecessary()

  try:
    device_list = _FindFuchsiaDevice(sdk_root, False)
  except OSError:
    logging.error('Fuchsia SDK Download failed. Please remove '
                  '%s and try again.', sdk_root)
    raise
  if not device_list:
    return []
  # Expected output will look something like
  # 'host0 target0\nhost1 target1\nhost2 target2'.
  first_device = device_list.splitlines()[0]
  host, target_name = first_device.split(' ')
  logging.info('Using Fuchsia device with address %s and name %s'
               % (host, target_name))
  return [FuchsiaDevice(target_name=target_name,
                        host=host,
                        system_log_file=options.fuchsia_system_log_file,
                        ssh_config=options.fuchsia_ssh_config,
                        port=options.fuchsia_ssh_port,
                        managed_repo=options.fuchsia_repo)]
