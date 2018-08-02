# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import os
import py_utils

from telemetry.core import util
from telemetry.internal.forwarders import Forwarder, ForwarderFactory


class FuchsiaForwarder(Forwarder):

  def __init__(self, interface, local, remote, _):
    super(FuchsiaForwarder, self).__init__()
    self._fi = interface

    if not local:
      local = util.GetUnreservedAvailableLocalPort()

    self._fi.ssh_forwarder.Map([(remote, local)])
    remote = self._fi.ssh_forwarder.GetDevicePortForHostPort(local)
    self._StartedForwarding(local, remote)
    py_utils.WaitFor(self._IsConnectionReady, timeout=60)

  def _IsConnectionReady(self):
    # The SSHPortForwarder.Map function blocks until the forwarding operation is
    # completed, so as soon as the forwarder's constructor is complete, it is
    # forwarding.
    return True

  def Close(self):
    self._fi.ssh_forwarder.Unmap(self.remote_port)
    super(FuchsiaForwarder, self).Close()


class FuchsiaForwarderFactory(ForwarderFactory):

  def __init__(self, fuchsia_interface):
    super(FuchsiaForwarderFactory, self).__init__()
    self.out_dir = os.path.join('./', 'out', 'fuchsia')
    self.arch = "x64"
    self._if = fuchsia_interface

  def Create(self, local_port, remote_port, reverse=True):
    """Creates a forwarder to map a remote (device) with a local (host) port.

    This forwarder factory produces forwarders that map a remote port to a free
    local port selected from the available ports on the host

    Args:
      local_port: A port on the local host
      remote_port: A port on the remote device
      reverse: A Boolean indicating the direction of the mapping.
    """
    return FuchsiaForwarder(self._if, local_port, remote_port, reverse)

  @property
  def host_ip(self):
    return '127.0.0.1'
