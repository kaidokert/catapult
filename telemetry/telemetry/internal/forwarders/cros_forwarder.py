# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import re
import subprocess
import tempfile

from telemetry.internal import forwarders
from telemetry.internal.forwarders import do_nothing_forwarder

import py_utils


class CrOsForwarderFactory(forwarders.ForwarderFactory):

  def __init__(self, cri):
    super(CrOsForwarderFactory, self).__init__()
    self._cri = cri

  def Create(self, local_port, remote_port, reverse=False):
    """Start forwarding between a pair of local and remote ports.

    This normally means mapping a known local_port to a remote_port. If the
    remote_port missing (e.g. 0 or None) then the forwarder will choose an
    available port on the device.

    Conversely, when reverse=True, a known remote_port is mapped to a
    local_port and, if this is missing, then the forwarder will choose an
    available port on the host.
    """
    if self._cri.local:
      return do_nothing_forwarder.DoNothingForwarder(local_port, remote_port)
    else:
      return CrOsSshForwarder(
          self._cri, local_port, remote_port, reverse)


class CrOsSshForwarder(forwarders.Forwarder):

  def __init__(self, cri, local_port, remote_port, reverse):
    super(CrOsSshForwarder, self).__init__()
    self._cri = cri
    self._proc = None

    if reverse:
      assert remote_port, 'Remote port must be given'
      if not local_port:
        local_port = util.GetUnreservedAvailableLocalPort()
    else:
      assert local_port, 'Local port must be given'
      remote_port = remote_port or 0

    forwarding_args = self._ForwardingArgs(local_port, remote_port, reverse)
    with tempfile.NamedTemporaryFile() as err_file:
      self._proc = subprocess.Popen(
          self._cri.FormSSHCommandLine(['-NT'], forwarding_args,
                                       port_forward=not reverse),
          stdout=subprocess.PIPE,
          stderr=err_file,
          stdin=subprocess.PIPE,
          shell=False)
      self._ForwardingStarted(local_port, remote_port)

      def _get_remote_port(err_file):
        # When we specify the remote port '0' in ssh remote port forwarding,
        # the remote ssh server should return the port it binds to in stderr.
        # e.g. 'Allocated port 42360 for remote forward to localhost:12345',
        # the port 42360 is the port created remotely and the traffic to the
        # port will be relayed to localhost port 12345.
        line = err_file.readline()
        tokens = re.search(r'port (\d+) for remote forward to', line)
        return int(tokens.group(1)) if tokens else None

      if not remote_port:
        with open(err_file.name, 'r') as err_file_reader:
          remote_port = py_utils.WaitFor(
              lambda: _get_remote_port(err_file_reader), timeout=60)

        # Update remote_port.
        self._ForwardingStarted(local_port, remote_port)

    py_utils.WaitFor(
        lambda: self._cri.IsHTTPServerRunningOnPort(self.remote_port), 60)

    logging.debug('Forwarding %s:%d to remote port %d (reverse=%s)',
        self.local_host, self.local_port, self.remote_port, reverse)

  def _ForwardingArgs(self, local_port, remote_port, reverse):
    if reverse:
      arg_format = '-L{local_port}:{local_host}:{remote_port}'
    else:
      arg_format = '-R{remote_port}:{local_host}:{local_port}'
    return [arg_format.format(local_host=self.local_host,
                              local_port=local_port,
                              remote_port=remote_port)]

  def Close(self):
    if self._proc:
      self._proc.kill()
      self._proc = None
    super(CrOsSshForwarder, self).Close()
