# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from telemetry.internal import forwarders
from telemetry.internal.forwarders import do_nothing_forwarder

import py_utils


class TestDoNothingForwarder(do_nothing_forwarder.DoNothingForwarder):
  """Override _WaitForConnect to avoid actual socket connection."""

  def __init__(self, *args, **kwargs):
    self.connected_ports = []
    super(TestDoNothingForwarder, self).__init__(*args, **kwargs)

  def _WaitForConnectionEstablished(self, timeout):
    self.connected_ports.append(self.local_port)


class TestErrorDoNothingForwarder(do_nothing_forwarder.DoNothingForwarder):
  """Simulate a connection error."""

  def _WaitForConnectionEstablished(self, timeout):
    raise py_utils.TimeoutException


class DoNothingForwarderTests(unittest.TestCase):
  def testBasicCheck(self):
    f = TestDoNothingForwarder(local_port=80, remote_port=80)
    self.assertEqual(f.connected_ports, [80])

  def testAutoCompletePort(self):
    # A missing port is auto-completed if possible.
    f = TestDoNothingForwarder(local_port=0, remote_port=80)
    self.assertEqual(f.connected_ports, [80])

  def testMissingPortsRaisesError(self):
    with self.assertRaises(do_nothing_forwarder.PortsMismatchError):
      # At least one of the ports must be given.
      TestDoNothingForwarder(local_port=0, remote_port=0)

  def testPortMismatchRaisesPortsMismatchError(self):
    with self.assertRaises(do_nothing_forwarder.PortsMismatchError):
      # The do_nothing_forward cannot forward from one port to another.
      TestDoNothingForwarder(local_port=80, remote_port=81)

  def testConnectionTimeoutRaisesConnectionError(self):
    with self.assertRaises(do_nothing_forwarder.ConnectionError):
      TestErrorDoNothingForwarder(local_port=80, remote_port=80)
