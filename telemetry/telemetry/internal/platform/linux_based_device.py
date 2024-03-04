# Copyright 2022 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import absolute_import
import logging
import os

from telemetry.core import platform
from telemetry.internal.platform import device
from telemetry.util import cmd_util


class LinuxBasedDevice(device.Device):

  OS_NAME = 'linux'
  OS_PROPER_NAME = 'Linux'
  GUID_NAME = 'linux'

  def __init__(self, host_name, ssh_port, ssh_identity, is_local):
    self.host_name = host_name
    if host_name == 'variable_skylab_device_hostname':
      print('found host_name of variable_skylab_device_hostname')
      bot_id = os.environ.get('SWARMING_BOT_ID')
      expected_prefix = 'cros-'
      if bot_id and bot_id.startswith(expected_prefix):
        self.host_name = bot_id[len(expected_prefix):]
      else:
        print('bot_id is %s' % bot_id)

    print('hostname is set to %s' % self.host_name)

    super().__init__(
        name=f'{self.OS_PROPER_NAME} with host {self.host_name or "localhost"}',
        guid=f'{self.GUID_NAME}:{self.host_name or "localhost"}')
    self._ssh_port = ssh_port
    self._ssh_identity = ssh_identity
    self._is_local = is_local

  @classmethod
  def GetAllConnectedDevices(cls, denylist):
    return []

  @classmethod
  def PlatformIsRunningOS(cls):
    return platform.GetHostPlatform().GetOSName() == cls.OS_NAME

  @classmethod
  def FindAllAvailableDevices(cls, options):
    use_ssh = options.remote and cmd_util.HasSSH()
    if not use_ssh and not cls.PlatformIsRunningOS():
      logging.debug('No --remote specified, and not running on %s.',
                    cls.OS_NAME)
      return []

    logging.debug('Found a linux based device')

    # TODO: This will assume all remote devices are valid, even
    # if not reachable
    return [
        cls(options.remote, options.remote_ssh_port,
            options.ssh_identity, not use_ssh)
    ]

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
