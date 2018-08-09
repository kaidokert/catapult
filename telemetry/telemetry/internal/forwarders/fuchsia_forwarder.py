# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# pylint: disable=bad-indentation

from telemetry.core import fuchsia_interface, util
from telemetry.internal.forwarders import Forwarder, ForwarderFactory

from fuchsia import net_test_server


class FuchsiaForwarder(Forwarder):

  def __init__(self, forwarder, is_local):
    super(FuchsiaForwarder, self).__init__()
    self._forwarder = forwarder

    if not is_local:
      is_local = util.GetUnreservedAvailableLocalPort()

    remote = self._forwarder.ForwardLocalPortAndGetRemote(is_local)
    self._StartedForwarding(is_local, remote)

  def _IsConnectionReady(self):
    # The SSHPortForwarder.Map function blocks until the forwarding operation is
    # completed, so as soon as the forwarder's constructor is complete, it is
    # forwarding.
    return True

  def Close(self):
    self._forwarder.ClearRemotePort(self.remote_port)
    super(FuchsiaForwarder, self).Close()

  def ForwardLocalPortAndGetRemote(self, local_port):
    self._forwarder.Map([(0, local_port)])
    return self._forwarder.GetDevicePortForHostPort(local_port)

  def ForwardAvailablePort(self):
    local = util.GetUnreservedAvailableLocalPort()
    remote = self.ForwardLocalPortAndGetRemote(local)
    return local, remote


class FuchsiaForwarderFactory(ForwarderFactory):

  # class member to hold created instances, mapping hostnames to class instances
  dev_instances = {}

  def __init__(self, device):
    super(FuchsiaForwarderFactory, self).__init__()
    self._out_dir = device._output_dir # pylint: disable=protected-access
    self._host = device._host # pylint: disable=protected-access
    self._ssh_forwarder = net_test_server.SSHPortForwarder(device)
    self.arch = "x64"

  def Create(self, local_port, remote_port, reverse=False):
    """Creates a forwarder to map a remote (device) with a local (host) port.

    This forwarder factory produces forwarders that map a remote port to a free
    local port selected from the available ports on the host

    Args:
      local_port (int): A port on the local host
      remote_port (int): A port on the remote device
      is_reverse (bool): Whether the port forwarding should be reversed or not.
    """

    return FuchsiaForwarder(self, local_port)

  @property
  def host_ip(self):
    return self._host


def GetForwarderFactory(fi):
  """GetForwarderFactory lazily initializes a single factory per device, which
  can be gotten multiple times to support many independent connections to one
  device without actually making as many objects"""
  if not fi.hostname in FuchsiaForwarderFactory.dev_instances:
    FuchsiaForwarderFactory.dev_instances[fi.hostname] = \
        FuchsiaForwarderFactory(fuchsia_interface)
  return FuchsiaForwarderFactory.dev_instances[fi.hostname]
