# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import absolute_import

from telemetry.internal.platform import device


class LinuxBasedDevice(device.Device):
  def __init__(self, name, guid, host_name, ssh_port, ssh_identity, is_local):
    super(LinuxBasedDevice, self).__init__(
        name=name,
        guid=guid)
    self._host_name = host_name
    self._ssh_port = ssh_port
    self._ssh_identity = ssh_identity
    self._is_local = is_local

  @classmethod
  def GetAllConnectedDevices(cls, denylist):
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

