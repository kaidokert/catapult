# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import logging
import socket

from telemetry.internal import forwarders

import py_utils


class Error(Exception):
  """Base class for exceptions in this module."""
  pass


class PortsMismatchError(Error):
  """Raised when local and remote ports are not equal."""
  pass


class ConnectionError(Error):
  """Raised when unable to connect to local TCP ports."""
  pass


class DoNothingForwarderFactory(forwarders.ForwarderFactory):

  def Create(self, local_port, remote_port, reverse=False):
    del reverse  # Not relevant for this forwarder.
    return DoNothingForwarder(local_port, remote_port)


class DoNothingForwarder(forwarders.Forwarder):
  """Check that no forwarding is needed for the given port pairs.

  The local and remote ports must be equal. Otherwise, the "do nothing"
  forwarder does not make sense. (Raises PortsMismatchError.)

  Also, check that all TCP ports support connections.  (Raises ConnectionError.)
  """

  def __init__(self, local_port, remote_port):
    super(DoNothingForwarder, self).__init__()
    local_port, remote_port = _ValidatePortValues(local_port, remote_port)
    self._ForwardingStarted(local_port, remote_port)
    self._WaitForConnectionEstablished()

  def _WaitForConnectionEstablished(self, timeout=10):
    address = (self.local_host, self.local_port)

    def CanConnect():
      with contextlib.closing(socket.socket()) as s:
        return s.connect_ex(address) == 0

    try:
      py_utils.WaitFor(CanConnect, timeout)
      logging.debug('Connection test succeeded for %s:%d', *address)
    except py_utils.TimeoutException:
      raise ConnectionError('Unable to connect to address: %s:%d' % address)


def _ValidatePortValues(local_port, remote_port):
  if not local_port:
    assert remote_port, 'Either local or remote ports must be given'
    local_port = remote_port
  elif not remote_port:
    remote_port = local_port
  elif local_port != remote_port:
    raise PortsMismatchError('Local port forwarding is not supported')
  return (local_port, remote_port)
