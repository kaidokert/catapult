# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#pylint: disable=bad-indentation
import logging

import os
import subprocess
from telemetry.internal.platform import device as device_mod
from telemetry.core import fuchsia_interface

if fuchsia_interface.FUCHSIA_IMPORT_SUCCESS:
  from fuchsia import boot_data
  from fuchsia.common import SDK_ROOT, DIR_SOURCE_ROOT


def _FindFuchsiaDeviceIp():
  # TODO(stephanstross): This is almost a line-for-line copy of __Discover in
  # build/fuchsia/device_target.py. That should be refactored to something more
  # general (and public) and imported.
  netaddr_path = os.path.join(SDK_ROOT, 'tools', 'netaddr')
  if not os.path.isfile(netaddr_path):
    return []
  command = [netaddr_path, '--fuchsia', '--nowait']
  logging.debug(' '.join(command))
  proc = subprocess.Popen(command,
                          stdout=subprocess.PIPE,
                          stderr=open(os.devnull, 'w'))
  out, _ = proc.communicate()
  if proc.returncode == 0:
    return out.decode('utf-8').splitlines()
  return []


class FuchsiaDevice(device_mod.Device):
  def __init__(self, host_name, ssh_config, is_local, out_dir_suffix):
    """POD class containing the info relevant to produce a DeviceTarget for the
    FuchsiaInterface class to use.

    Arguments:
      host_name (str): The IP address or hostname of the device
      ssh_config (path): The path to the SSH config needed to talk to the device
      is_local (bool): Whether or not the device is a QEMU instance or physical
                       hardware
      out_dir_suffix (path): The path suffix, relative to the chromium/src
                             directory, containing fuchsia build files.
    """
    super(FuchsiaDevice, self).__init__(
        name='Fuchsia with host %s' % host_name,
        guid='zircon:%s' % host_name)
    self._host_name = host_name
    self._ssh_port = 0
    self._ssh_config = ssh_config
    self._ssh_identity = None
    self._is_local = is_local
    self._out_dir_suffix = out_dir_suffix

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

  @property
  def out_dir_suffix(self):
    return self._out_dir_suffix

def FindAllAvailableDevices(options):
  """Returns a list containing any found remote fuchsia device, or one
  corresponding to the --remote flag."""
  if options.remote:
    dev_ips = [options.remote]
  elif options.discover_fuchsia:
    dev_ips = _FindFuchsiaDeviceIp()
  else:
    return []

  if options.fuchsia_out_dir_suffix:
    out_dir = os.path.join(DIR_SOURCE_ROOT, options.fuchsia_out_dir_suffix)
  else:
    return []

  expected_ssh_config_path = boot_data.GetSSHConfigPath(out_dir)

  if options.ssh_config:
    conf_path = options.ssh_config
  elif os.path.exists(expected_ssh_config_path):
    conf_path = expected_ssh_config_path
  else:
    raise Exception("A good SSH config path wasn't specified in command line "
                    "options, and the default config file (%s) does not exist!"
                    % expected_ssh_config_path)

  conf_path = os.path.abspath(conf_path)
  devices = []
  for dev_ip in dev_ips:
    device = FuchsiaDevice(dev_ip, conf_path, False, out_dir)
    devices.append(device)
  return devices
