# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections


PortSet = collections.namedtuple('PortSet', ['http', 'https', 'dns'])



class ForwarderFactory(object):

  def Create(self, local_port, remote_port, reverse=False):
    """Creates a forwarder that maps local (host) <-> remote (device) ports.

    Args:
      local_port: A port to forward on the host machine.
      remote_port: A port to forward on the remote machine.
      reverse: Whether to map ports from device to host.
    """
    raise NotImplementedError()

  #@property  -  killing it to se who complains
  #def host_ip(self):
  #  return '127.0.0.1'


class Forwarder(object):

  def __init__(self):
    self._local_port = None
    self._remote_port = None
    self._forwarding = False

  def _ForwardingStarted(local_port, remote_port):
    self._local_port = local_port
    self._remote_port = remote_port
    self._forwarding = True

  #@property
  #def host_port(self):
  #  return self._port_pair.remote_port

  #@property
  #def host_ip(self):
  #  return '127.0.0.1'

  @property
  def local_host(self):
    return '127.0.0.1'

  @property
  def local_port(self):
    return self._local_port

  @property
  def reomte_port(self):
    return self._remote_port

  @property
  def is_active(self):
    return self._forwarding

  #@property
  #def host_url(self):
  #  assert self.host_ip and self.host_port
  #  return 'http://%s:%i' % (self.host_ip, self.host_port)

  def Close(self):
    self._local_port = None
    self._remote_port = None
    self._forwarding = False
