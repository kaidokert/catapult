# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import os
import sys
from telemetry.internal.platform import device


BUILD_FUCHSIA = os.path.abspath(os.path.join('./', 'build', 'fuchsia'))
sys.path.append(BUILD_FUCHSIA)

import boot_data

_DEFAULT_FUCHSIA_IP = '192.168.42.64'
_OUT_DIR = os.path.abspath('./out/fuchsia')
_DEFAULT_SSH_CONFIG = boot_data.GetSSHConfigPath(_OUT_DIR)

class FuchsiaDevice(device.Device):
  def __init__(self, host_name, ssh_port, ssh_config, is_local):
    if not host_name:
      host_name = _DEFAULT_FUCHSIA_IP
    super(FuchsiaDevice, self).__init__(
        name='Fuchsia with host %s' % host_name,
        guid='zircon:%s' % host_name)
    self.host_name = host_name
    self.ssh_port = ssh_port
    self.ssh_config = ssh_config
    self._ssh_identity = None
    self._is_local = is_local

  @classmethod
  def GetAllConnectedDevices(cls, blacklist):
    return []

  @property
  def host_name(self):
    return self.host_name

  @property
  def ssh_port(self):
    return self.ssh_port

  @property
  def ssh_identity(self):
    return self._ssh_identity

  @property
  def is_local(self):
    return self._is_local

def FindAllAvailableDevices(options):
  """Returns a list containing the default remote fuchsia device."""
  dev_ip = options.remote if options.remote else _DEFAULT_FUCHSIA_IP
  if options.ssh_config:
    conf_path = options.ssh_config
  elif os.path.exists(_DEFAULT_SSH_CONFIG):
    conf_path = _DEFAULT_SSH_CONFIG
  else:
    raise Exception("A good SSH config path wasn't specified in command line "
                    "options, and the default config file (%s) does not exist!"
                    % _DEFAULT_SSH_CONFIG)

  return [FuchsiaDevice(dev_ip, 22, conf_path, False)]
