# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import os
import sys


BUILD_FUCHSIA = os.path.abspath(os.path.join('./', 'build', 'fuchsia'))
sys.path.append(BUILD_FUCHSIA)

import boot_data
from device_target import DeviceTarget
from telemetry.internal.forwarders import Forwarder, ForwarderFactory


import logging


class FuchsiaForwarder(Forwarder):

  def __init__(self, dev, port):
    super(FuchsiaForwarder, self).__init__()
    self._remote_port = port
    self.device = dev
    self.EnsureStart()

  def _StartedForwarding(self, local_port, remote_port):
    assert not self.is_forwarding, 'forwarder has already started'
    assert local_port and remote_port, 'ports should now be determined'

    self._local_port = local_port
    self._remote_port = remote_port
    logging.info('%s started between %s:%s and %s', type(self).__name__,
                 self.host_ip, self.local_port, self.remote_port)

  @property
  def is_forwarding(self):
    return self.device.IsStarted()

  @property
  def local_port(self):
    return None

  @property
  def remote_port(self):
    return self._remote_port

  def Close(self):
    self._remote_port = None
    self.device = None

  def RunCommand(self, command, silent=False):
    return self.device.RunCommand(command, silent=silent)

  def RunCommandPiped(self, command, **popen_kwargs):
    return self.device.RunCommandPiped(command, **popen_kwargs)

  def EnsureStart(self):
    if self.device.IsStarted():
      return
    self.device.Start()


class FuchsiaForwarderFactory(ForwarderFactory):

  def __init__(self):
    super(FuchsiaForwarderFactory, self).__init__()
    self.out_dir = os.path.join('./', 'out', 'fuchsia')
    self.arch = "x64"

  def Create(self, local_port, remote_port, reverse=True):
    """Creates a forwarder to map a remote (device) with a local (host) port.

    This forwarder factory produces forwarders that map a remote port to a free
    local port selected from the available ports on the host

    Args:
      local_port: An http port on the local host. We ignore this, but the arg is
          still in to not screw up the inheritance.
      remote_port: An http port on the remote device.
      reverse: A Boolean indicating the direction of the mapping.
    """
    if not reverse or local_port != 0:
      logging.warn("The FuchsiaForwarderFactory does not currently support "
                   "non-reverse connection to a device. reverse=False and all "
                   "local_port settings will be ignored. port: %s, reverse: %s",
                   local_port, reverse)
    ssh_config = boot_data.GetSSHConfigPath(self.out_dir)
    dev = DeviceTarget(self.out_dir, self.arch, host='192.168.42.64',
                       port=remote_port, ssh_config=ssh_config)
    dev._auto = True
    return FuchsiaForwarder(dev, remote_port)

  @property
  def host_ip(self):
    return '127.0.0.1'
