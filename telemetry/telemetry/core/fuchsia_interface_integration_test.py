# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import subprocess
import tempfile
import unittest

from telemetry.core import fuchsia_interface
from telemetry import decorators
from telemetry.internal.platform import fuchsia_device
from telemetry.testing import options_for_unittests


class FuchsiaInterfaceTest(unittest.TestCase):

  def setUp(self):
    fake_options = options_for_unittests.GetCopy()
    self.device = fuchsia_device.FindAllAvailableDevices(fake_options)
    self.interface = fuchsia_interface.FuchsiaInterface(self.device)

  @decorators.Enabled('fuchsia')
  def testPushContents(self):
    with tempfile.NamedTemporaryFile('w') as tmp_file:
      test_contents = 'hello world'
      tmp_file.write(test_contents)

      self.interface.PutFile(tmp_file.name, '/tmp')
      real_contents = self.interface.ReadFile('/tmp/%s' % tmp_file.name)
      self.assertTrue(real_contents == test_contents)

  @decorators.Enabled('fuchsia')
  def testExists(self):
    # These assertTrue statements ensure that the more important directories on
    # the fuchsia device exist.
    self.assertTrue(self.interface.PathExists('/blob'))
    self.assertTrue(self.interface.PathExists('/boot'))
    self.assertTrue(self.interface.PathExists('/data'))
    self.assertTrue(self.interface.PathExists('/tmp'))
    # This makes sure that PathExists works as expected and doesn't erroneously
    # report True on things that don't actually exist
    self.assertFalse(self.interface.PathExists('/wubbalubbadubdub'))

  @decorators.Enabled('fuchsia')
  def testIsServiceRunning(self):
    self.assertTrue(self.interface.IsProcessRunning('bin/devmgr'))

  @decorators.Disabled('all')
  def testGetRemotePortAndIsHTTPServerRunningOnPort(self):
    local, remote = self.interface.ForwardAvailablePort()

    test_string = "Hello, World!"
    # Send command to fuchsia to listen on the forwarded port
    remote_netcat = self.interface.RunCommandPiped(['nc', '-l', str(remote)])

    local_netcat = subprocess.Popen('nc', 'localhost', str(local))
    local_netcat.stdin.write(test_string)
    local_netcat.kill()

    out, _ = remote_netcat.communicate()
    self.assertTrue(out == test_string)

  @decorators.Enabled('fuchsia')
  def testGetRemotePortReservedPorts(self):
    _, remote_1 = self.interface.ForwardAvailablePort()
    _, remote_2 = self.interface.ForwardAvailablePort()

    self.assertTrue(remote_1 != remote_2)
