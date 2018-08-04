# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import logging
import py_utils

from telemetry.core import fuchsia_interface, util
from telemetry.internal.forwarders import Forwarder, ForwarderFactory


class FuchsiaForwarder(Forwarder):

  def __init__(self, interface, local):
    super(FuchsiaForwarder, self).__init__()
    self._fi = interface

    if not local:
      local = util.GetUnreservedAvailableLocalPort()

    remote = self._fi.ForwardLocalPortAndGetRemote(local)
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

  # class member to hold created instances, mapping hostnames to class instances
  dev_instances = {}

  def __init__(self, fi):
    super(FuchsiaForwarderFactory, self).__init__()
    self.out_dir = fuchsia_interface.OUT_DIR
    self.arch = "x64"
    self._fi = fi

  def Create(self, local_port, remote_port, reverse=True):
    """Creates a forwarder to map a remote (device) with a local (host) port.

    This forwarder factory produces forwarders that map a remote port to a free
    local port selected from the available ports on the host

    Args:
      local_port: A port on the local host
      remote_port: A port on the remote device
      reverse: A Boolean indicating the direction of the mapping.
    """
    if remote_port:
      logging.warn('The fuchsia forwarder only uses the local port. '
                   'The specified remote port will be ignored')

    if not reverse:
      logging.warn('The fuchsia forwarder currently only sets up reverse '
                   'ssh port forwarding connections')

    return FuchsiaForwarder(self._fi, local_port)

  @property
  def host_ip(self):
    return '127.0.0.1'


def GetForwarderFactory(fi):
  """GetForwarderFactory lazily initializes a single factory per device, which
  can be gotten multiple times to support many independent connections to one
  device without actually making as many objects"""
  if not fi.hostname in FuchsiaForwarderFactory.dev_instances:
    FuchsiaForwarderFactory.dev_instances[fi.hostname] = \
        FuchsiaForwarderFactory(fuchsia_interface)
  return FuchsiaForwarderFactory.dev_instances[fi.hostname]
