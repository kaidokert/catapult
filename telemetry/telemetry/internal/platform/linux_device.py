# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import absolute_import
import logging

from telemetry.core import platform
from telemetry.internal.platform import linux_based_device
from telemetry.util import cmd_util


class LinuxDevice(linux_based_device.LinuxBasedDevice):
  def __init__(self, host_name, ssh_port, ssh_identity, is_local):
    super(LinuxDevice, self).__init__(
        name='LinuxDevice with host %s' % host_name or 'localhost',
        guid='linux:%s' % host_name or 'localhost',
    host_name=host_name,
    ssh_port=ssh_port,
    ssh_identity=ssh_identity,
    is_local=is_local)


def IsRunningOnLinux():
  return platform.GetHostPlatform().GetOSName() == 'linux'


def FindAllAvailableDevices(options):
  """Returns a list of available device types."""
  use_ssh = options.cros_remote and cmd_util.HasSSH()
  if not use_ssh and not IsRunningOnLinux():
    logging.debug('No --remote specified, and not running on linux.')
    return []

  return [LinuxDevice(options.cros_remote, options.cros_remote_ssh_port,
                     options.cros_ssh_identity, not use_ssh)]
