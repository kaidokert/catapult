# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import tempfile

from telemetry.core import util
from telemetry.internal import forwarders
from telemetry.internal.forwarders.forwarder_utils import (
    ForwardingArgs,
    ReadRemotePort,
)

class FuchsiaForwarderFactory(forwarders.ForwarderFactory):

  def __init__(self, command_runner):
    super(FuchsiaForwarderFactory, self).__init__()
    self._command_runner = command_runner

  def Create(self, local_port, remote_port, reverse=False):
    return FuchsiaSshForwarder(local_port, remote_port,
                               self._command_runner,
                               port_forward=not reverse)

class FuchsiaSshForwarder(forwarders.Forwarder):

  def __init__(self, local_port, remote_port, command_runner, port_forward):
    super(FuchsiaSshForwarder, self).__init__()
    self._proc = None

    if port_forward:
      assert local_port, 'Local port must be given'
    else:
      assert remote_port, 'Remote port must be given'
      if not local_port:
        # Choose an available port on the host.
        local_port = util.GetUnreservedAvailableLocalPort()

    forward_cmd = [
        '-O', 'forward',  # Send SSH mux control signal.
        '-N',  # Don't execute command
        '-T'  # Don't allocate terminal.
    ]

    forward_cmd.append(ForwardingArgs(
        local_port, remote_port, self.host_ip, port_forward))

    with tempfile.NamedTemporaryFile() as stderr_file:
      self._proc = command_runner.RunCommandPiped(forward_cmd)
      if not remote_port:
        remote_port = ReadRemotePort(stderr_file.name)

    self._StartedForwarding(local_port, remote_port)

  def Close(self):
    if self._proc:
      self._proc.kill()
      self._proc = None
    super(FuchsiaSshForwarder, self).Close()
