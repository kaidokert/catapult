# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import logging
import os

from telemetry.internal.forwarders import Forwarder, ForwarderFactory


class FuchsiaForwarder(Forwarder):

  def __init__(self):
    super(FuchsiaForwarder, self).__init__()
    self._remote_port = None
    self._local_port = None


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
    return FuchsiaForwarder()

  @property
  def host_ip(self):
    return '127.0.0.1'
