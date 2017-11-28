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
    del reverse  # Irrelevant for DoNothingForwarder.
    return DoNothingForwarder(local_port, remote_port)


def _ValidatePortValues(local_port, remote_port):
  if not local_port:
    if not remote_port:
      raise PortsMismatchError(
          'Either local_port or remote_port must be given')
    local_port = remote_port
  elif not remote_port:
    remote_port = local_port
  if local_port != remote_port:
    raise PortsMismatchError('Local port forwarding is not supported')
  return (local_port, remote_port)


def _CheckLocalPortSupportsConnections(local_port, timeout=10):
  def CanConnect():
    with contextlib.closing(socket.socket()) as s:
      return s.connect_ex((_LOCAL_HOST, local_port)) == 0

  try:
    py_utils.WaitFor(CanConnect, timeout)
    logging.debug(
        'Connection test succeeded for %s:%d', _LOCAL_HOST, local_port)
  except py_utils.TimeoutException
  


class DoNothingForwarder(forwarders.Forwarder):
  """Check that no forwarding is needed for the given port pairs.

  The local and remote ports must be equal. Otherwise, the "do nothing"
  forwarder does not make sense. (Raises PortsMismatchError.)

  Also, check that all TCP ports support connections.  (Raises ConnectionError.)

  Either local_port or remote_port may be missing, but not both.
  """
  LOCAL_HOST = ''

  def __init__(self, local_port, remote_port):
    super(DoNothingForwarder, self).__init__()
    local_port, remote_port = _ValidatePorts(local_port, remote_port)
    _CheckPortSupportsConnections(local_port)
    self._ForwardingStarted(local_port, remote_port)

  def _CheckPortPair(self):
    try:
      self._WaitForConnectionEstablished(timeout=10)
      logging.debug(
          'Connection test succeeded for %s:%d',
          self.local_host, self.local_port)
    except py_utils.TimeoutException:
      raise ConnectionError(
          'Unable to connect to address: %s:%d',
          self.local_host, self.local_port)

  def _WaitForConnectionEstablished(self, timeout):
    py_utils.WaitFor(CanConnect, timeout)
