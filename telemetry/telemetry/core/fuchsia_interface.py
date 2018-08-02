# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""A wrapper around DeviceTarget for common operations within Catapult on
Fuchsia"""
import os
import sys

# Common paths needed to work with Fuchsia

_UP_SIX_DIRS = [os.pardir] * 6
CHROMIUM_SRC = os.path.abspath(os.path.join(__file__, *_UP_SIX_DIRS))
assert os.path.basename(CHROMIUM_SRC) == 'src', (
    'Did not climb up to the chromium/src/ directory!Instead reaches %s. This'
    ' will probably not work correctly!' % CHROMIUM_SRC)
_BUILD_FUCHSIA = os.path.join(CHROMIUM_SRC, 'build', 'fuchsia')
OUT_DIR = os.path.abspath(os.path.join(CHROMIUM_SRC, 'out', 'fuchsia'))
sys.path.append(_BUILD_FUCHSIA)

from device_target import DeviceTarget
from net_test_server import SSHPortForwarder
from run_package import RunPackage

class FuchsiaInterface(object):
  "FuchsiaInterface manages communication with a remote Fuchsia device."
  def __init__(self, device):
    self._hostname = device.host_name
    self._ssh_port = device.ssh_port
    self._ssh_config = device.ssh_config
    self._device = DeviceTarget(OUT_DIR, "x64",
                                host=self._hostname,
                                port=self._ssh_port,
                                ssh_config=self._ssh_config)
    self.ssh_forwarder = SSHPortForwarder(self._device)
    self._device._auto = True
    self._device.Start()
    self._InstallBrowser()

  def _InstallBrowser(self):
    name = 'content_shell'
    far_path = os.path.join(OUT_DIR,
                            'gen/content/shell/content_shell/content_shell.far')
    RunPackage(OUT_DIR, self._device, far_path, name, [], [], False, True)

  def RunCommandPiped(self, command, **popen_kwargs):
    return self._device.RunCommandPiped(command, **popen_kwargs)

  def RunCommand(self, command, silent=False):
    return self._device.RunCommand(command, silent=silent)

  def IsStarted(self):
    return self._device.IsStarted()

  def EnsureStart(self):
    self._device.Start()

  @property
  def local(self):
    return not self._hostname

  @property
  def hostname(self):
    return self._hostname

  @property
  def ssh_port(self):
    return self._ssh_port
