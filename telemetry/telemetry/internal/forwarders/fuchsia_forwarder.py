# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import logging
import os
import py_utils
import re
import subprocess

from telemetry.internal.forwarders import Forwarder, ForwarderFactory


class FuchsiaForwarder(Forwarder):

  def __init__(self, interface, local):
    super(FuchsiaForwarder, self).__init__()
    self._fi = interface

    self._fi.ssh_forwarder.Map([(0, local)])
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


def _ReadRemotePort(filename):
  def TryReadingPort(f):
    # When we specify the remote port '0' in ssh remote port forwarding,
    # the remote ssh server should return the port it binds to in stderr.
    # e.g. 'Allocated port 42360 for remote forward to localhost:12345',
    # the port 42360 is the port created remotely and the traffic to the
    # port will be relayed to localhost port 12345.
    line = f.readline()
    tokens = re.search(r'port (\d+) for remote forward to', line)
    return int(tokens.group(1)) if tokens else None

  with open(filename, 'r') as f:
    return py_utils.WaitFor(lambda: TryReadingPort(f), timeout=60)


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
      local_port: An http port on the local host. We ignore this, but the arg is
          still in to not screw up the inheritance.
      remote_port: An http port on the remote device, which will be ignored
      reverse: A Boolean indicating the direction of the mapping.
    """
    if remote_port:
      logging.warn("The remote port option will be ignored")
    if not reverse:
      raise ValueError("The Fuchsia Forwarder only supports reverse connection")
    if not local_port:
      raise ValueError("The local port for the fuchsia forwarder must not be "
                       "zero!")
    return FuchsiaForwarder(self._if, local_port)

  @property
  def host_ip(self):
    return '127.0.0.1'
