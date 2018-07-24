# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from telemetry.internal.platform import device

_DEFAULT_FUCHSIA_IP = '192.168.42.64'

class FuchsiaDevice(device.Device):
  def __init__(self, host_name, ssh_port, ssh_identity, is_local):
    if not host_name:
      host_name = _DEFAULT_FUCHSIA_IP
    super(FuchsiaDevice, self).__init__(
        name='Fuchsia with host %s' % host_name,
        guid='zircon:%s' % host_name)
    self._host_name = host_name
    self._ssh_port = ssh_port
    self._ssh_identity = ssh_identity
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
  def ssh_identity(self):
    return self._ssh_identity

  @property
  def is_local(self):
    return self._is_local

def FindAllAvailableDevices(options):
  """Returns a list containing the default remote fuchsia device."""

  return [FuchsiaDevice(None, 22, options.cros_ssh_identity, False)]
