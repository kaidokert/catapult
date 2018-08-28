# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# pylint: disable=bad-indentation

import re
import subprocess

from telemetry.core import fuchsia_interface, util
from telemetry.internal.forwarders import Forwarder, ForwarderFactory

PORT_MAP_RE = re.compile('Allocated port (?P<port>\d+) for remote')
GET_PORT_NUM_TIMEOUT_SECS = 5


class FuchsiaForwarder(Forwarder):
  def __init__(self, forwarder, host, device, reverse):
    super(FuchsiaForwarder, self).__init__()
    self._forwarder = forwarder
    self._reverse = reverse
    host, device = self._forwarder.Map(host, device, reverse)
    self._StartedForwarding(host, device)

  def _IsConnectionReady(self):
    #ForwardPort always blocks until it finishes
    return True

  def Close(self):
    self._forwarder.Unmap(self._local_port, self._remote_port, self._reverse)
    super(FuchsiaForwarder, self).Close()


class FuchsiaForwarderFactory(ForwarderFactory):

  # class member to hold created instances, mapping hostnames to class instances
  dev_instances = {}

  def __init__(self, iface):
    super(FuchsiaForwarderFactory, self).__init__()
    self._iface = iface
    self._port_map = {}
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

    return FuchsiaForwarder(self, local_port, remote_port, reverse)

  def GetDevicePortForHostPort(self, host_port):
    if host_port in self._port_map:
      return self._port_map[host_port]

  def Unmap(self, host, device, reverse):
    # Make sure we're not trying to unmap something we didn't make.
    assert host in self._port_map and device == self._port_map[host]
    #Default arguments
    forwarding_args = ['-NT', '-O', 'cancel']
    if reverse:
      forwarding_args += ['-R', '{}:localhost:{}'.format(device, host)]
    else:
      forwarding_args += ['-L', '{}:localhost:{}'.format(host, device)]
    task = self._iface.RunCommandPiped([],
                                       ssh_args=forwarding_args,
                                       stderr=subprocess.PIPE)
    task.wait()
    if task.returncode != 0:
      raise Exception(
          'Error {} when unmapping port {}'.format(task.returncode, device))
    del self._port_map[host]
    return

  @property
  def host_ip(self):
    return self._iface.hostname

  def Map(self, host, device, reverse):
    # This has to be flipped because Telemetry uses opposite terminology to SSH.
    reverse = not reverse

    if reverse:
      # Sanity check, only the device port should be given.
      assert host and not device
      device = 0
      forwarding_scheme = ['-R', '{}:localhost:{}'.format(device, host)]
    else:
      # Again, sanity check.
      assert device and not host
      host = util.GetUnreservedAvailableLocalPort()
      forwarding_scheme = ['-L', '{}:localhost:{}'.format(host, device)]

    forwarding_flags = forwarding_scheme + [
        '-O', 'forward', # Send signal to SSH Muxer
        '-v', # Get forwarded port info from stderr.
        '-NT'] # Don't execute command; don't allocate terminal.

    _, err = self._iface.RunCommandPiped([],
                                         ssh_args=forwarding_flags,
                                         stderr=subprocess.PIPE).communicate()
    if not device:
      for line in err.split('\n'):
        matched = PORT_MAP_RE.match(line)
        if matched:
          device = int(matched.group('port'))
          break
    self._port_map[host] = device
    return host, device


def GetForwarderFactory(fi):
  """GetForwarderFactory lazily initializes a single factory per device, which
  can be gotten multiple times to support many independent connections to one
  device without actually making as many objects"""
  if not fi.hostname in FuchsiaForwarderFactory.dev_instances:
    FuchsiaForwarderFactory.dev_instances[fi.hostname] = \
        FuchsiaForwarderFactory(fuchsia_interface)
  return FuchsiaForwarderFactory.dev_instances[fi.hostname]
