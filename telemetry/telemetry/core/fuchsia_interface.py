# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""A wrapper around DeviceTarget for common operations within Catapult on
Fuchsia"""
import os
import sys


BUILD_FUCHSIA = os.path.abspath(os.path.join('./', 'build', 'fuchsia'))
OUT_DIR = os.path.abspath(os.path.join('./', 'out', 'fuchsia'))
sys.path.append(BUILD_FUCHSIA)

import boot_data
from device_target import DeviceTarget

class FuchsiaInterface(object):
  "FuchsiaInterface manages communication with a remote Fuchsia device."
  def __init__(self, device):
    self._host_name = device.host_name
    self._ssh_port = device.ssh_port
    self._ssh_config = device.ssh_config
    self._device = DeviceTarget(OUT_DIR, "x64",
                                host=self._host_name,
                                port=self._ssh_port,
                                ssh_config=self._ssh_config)
    self._device._auto = True

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
    return not self._host_name

  @property
  def hostname(self):
    return self._host_name

  @property
  def ssh_port(self):
    return self._ssh_port
