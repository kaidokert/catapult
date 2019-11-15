# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import mock

from telemetry.internal.forwarders import cros_forwarder


class CrOsSshForwarderTests(unittest.TestCase):
  def setUp(self):
    self._Patch('subprocess')  # Do not actually run subprocesses.
    self._Patch('tempfile')  # Do not actually create tempfiles.
    self.ReadRemotePort = self._Patch('ReadRemotePort')
    self.GetUnreservedAvailableLocalPort = self._Patch(
        'util.GetUnreservedAvailableLocalPort')
    self.cri = mock.Mock()

  def _Patch(self, target):
    patcher = mock.patch(
        'telemetry.internal.forwarders.cros_forwarder.' + target)
    self.addCleanup(patcher.stop)
    return patcher.start()

  def testForwarderBasic(self):
    f = cros_forwarder.CrOsSshForwarder(
        self.cri, local_port=111, remote_port=222, port_forward=True)
    self.cri.FormSSHCommandLine.assert_called_once_with(
        ['-NT'], ['-o', 'LogLevel=INFO', '-R222:127.0.0.1:111'],
        port_forward=True)
    self.assertEqual(f.local_port, 111)
    self.assertEqual(f.remote_port, 222)

  def testForwarderBasicReverse(self):
    f = cros_forwarder.CrOsSshForwarder(
        self.cri, local_port=111, remote_port=222, port_forward=False)
    self.cri.FormSSHCommandLine.assert_called_once_with(
        ['-NT'], ['-o', 'LogLevel=INFO', '-L111:127.0.0.1:222'],
        port_forward=False)
    self.assertEqual(f.local_port, 111)
    self.assertEqual(f.remote_port, 222)

  def testForwarderDefaultRemote(self):
    self.ReadRemotePort.return_value = 444
    f = cros_forwarder.CrOsSshForwarder(
        self.cri, local_port=111, remote_port=None, port_forward=True)
    self.cri.FormSSHCommandLine.assert_called_once_with(
        ['-NT'], ['-o', 'LogLevel=INFO', '-R0:127.0.0.1:111'],
        port_forward=True)
    self.assertEqual(f.local_port, 111)
    self.assertEqual(f.remote_port, 444)

  def testForwarderReverseDefaultLocal(self):
    self.GetUnreservedAvailableLocalPort.return_value = 777
    f = cros_forwarder.CrOsSshForwarder(
        self.cri, local_port=None, remote_port=222, port_forward=False)
    self.cri.FormSSHCommandLine.assert_called_once_with(
        ['-NT'], ['-o', 'LogLevel=INFO', '-L777:127.0.0.1:222'],
        port_forward=False)
    self.assertEqual(f.local_port, 777)
    self.assertEqual(f.remote_port, 222)

