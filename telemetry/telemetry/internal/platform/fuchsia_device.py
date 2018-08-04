# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import logging
import os
import subprocess
from telemetry.internal.platform import device
from telemetry.core.fuchsia_interface import CHROMIUM_SRC, OUT_DIR

import boot_data

_DEFAULT_SSH_CONFIG = boot_data.GetSSHConfigPath(OUT_DIR)

def _FindFuchsiaDevice():
  # TODO(stephanstross): This is almost a line-for-line copy of __Discover in
  # build/fuchsia/device_target.py. That should be refactored to something more
  # general (and public) and imported.
  netaddr_path = os.path.join(CHROMIUM_SRC, 'third_party', 'fuchsia-sdk',
                              'sdk', 'tools', 'netaddr')
  command = [netaddr_path, '--fuchsia', '--nowait']
  logging.debug(' '.join(command))
  proc = subprocess.Popen(command,
                          stdout=subprocess.PIPE,
                          stderr=open(os.devnull, 'w'))
  proc.wait()
  if proc.returncode == 0:
    return proc.stdout.readlines()[0].strip()
  return '192.168.42.64'

_DEFAULT_FUCHSIA_IP = _FindFuchsiaDevice()


class FuchsiaDevice(device.Device):
  def __init__(self, host_name, ssh_config, is_local):
    if not host_name:
      host_name = _DEFAULT_FUCHSIA_IP
    super(FuchsiaDevice, self).__init__(
        name='Fuchsia with host %s' % host_name,
        guid='zircon:%s' % host_name)
    self._host_name = host_name
    self._ssh_port = 0
    self._ssh_config = ssh_config
    self._ssh_identity = None
    self._is_local = is_local

  @classmethod
  def GetAllConnectedDevices(cls, blacklist):
    return []

  @property
  def host_name(self):
    return self._host_name

  @property
  def ssh_port(self):
    return self._ssh_port

  @property
  def ssh_config(self):
    return self._ssh_config

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

  return [FuchsiaDevice(dev_ip, conf_path, False)]
