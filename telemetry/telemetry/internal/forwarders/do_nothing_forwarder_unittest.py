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

  def _WaitForConnectionEstablished(self, timeout=10):
    self.connected_ports.append(self.local_port)


class TestErrorDoNothingForwarder(do_nothing_forwarder.DoNothingForwarder):
  """Simulate a connection error."""

  def _WaitForConnectionEstablished(self, timeout=10):
    raise py_utils.TimeoutException


class DoNothingForwarderTests(unittest.TestCase):
  def testBasicCheck(self):
    f = TestDoNothingForwarder(local_port=80, remote_port=80)
    self.assertEqual(f.connected_addresses, [80])
    self.assertEqual(f.local_port, f.remote_port)

  def testDefaultLocalPort(self):
    f = TestDoNothingForwarder(local_port=0, remote_port=80)
    self.assertEqual(f.connected_addresses, [80])
    self.assertEqual(f.local_port, f.remote_port)

  def testDefaultLocalPort(self):
    f = TestDoNothingForwarder(local_port=80, remote_port=None)
    self.assertEqual(f.connected_addresses, [80])
    self.assertEqual(f.local_port, f.remote_port)

  def testBothPortsMissingRaisesError(self):
    with self.assertRaises(AssertionError):
      TestDoNothingForwarder(local_port=0, remote_port=0)

  def testPortMismatchRaisesPortsMismatchError(self):
    # The do_nothing_forward cannot forward from one port to another.
    with self.assertRaises(do_nothing_forwarder.PortsMismatchError):
      TestDoNothingForwarder(local_port=80, remote_port=81)

  def testConnectionTimeoutRaisesConnectionError(self):
    with self.assertRaises(do_nothing_forwarder.ConnectionError):
      TestErrorDoNothingForwarder(local_port=80, remote_port=80)
