# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections


PortSet = collections.namedtuple('PortSet', ['http', 'https', 'dns'])



class ForwarderFactory(object):

  def Create(self, local_port, remote_port, reverse=False):
    """Create a forwarder to map a local (host) with a remote (device) port.

    Args:
      local_port: The port on the local host.
      remote_port: The port on the remote device.
      reverse: Whether the connection should be mapped from the device back to
          the host.
    """
    raise NotImplementedError()

  #@property
  #def host_ip(self):
  #  return '127.0.0.1'


class Forwarder(object):

  def __init__(self):
    self._port_mapping = None

  def _ForwardingStarted(local_port, remote_port):
    self._port_mapping = (local_port, remote_port)

  #@property
  #def host_port(self):
  #  return self._port_pair.remote_port

  @property
  def local_host(self):
    return '127.0.0.1'

  @property
  def is_forwarding(self):
    return self._port_mapping is not None

  @property
  def local_port(self):
    return self._port_mapping[0] if self.is_forwarding else None

  @property
  def remote_port(self):
    return self._port_mapping[1] if self.is_forwarding else None

  #@property
  #def url(self):
  #  assert self.host_ip and self.host_port
  #  return 'http://%s:%i' % (self.host_ip, self.host_port)

  def Close(self):
    self._port_mapping = None
