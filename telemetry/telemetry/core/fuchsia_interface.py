# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#pylint: disable=bad-indentation
"""A wrapper around DeviceTarget for common operations within Catapult on
Fuchsia"""

# Necessary path changes to access Fuchsia utilities in chromium repo
import os
import sys
if os.path.basename(os.getcwd()) == 'src':
  build_dir = os.path.join(os.getcwd(), 'build')
  if os.path.exists(build_dir):
    sys.path.append(build_dir)
    FUCHSIA_IMPORT_SUCCESS = True
  else:
    FUCHSIA_IMPORT_SUCCESS = False


if FUCHSIA_IMPORT_SUCCESS:
  from fuchsia import device_target


class FuchsiaInterface(object):
  "FuchsiaInterface manages communication with a remote Fuchsia device."
  def __init__(self, device):
    self._hostname = device.host_name
    self._ssh_port = device.ssh_port
    self._ssh_config = device.ssh_config
    self._out_dir = device.out_dir_suffix
    self._device = device_target.DeviceTarget(self._out_dir, "x64",
                                              host=self._hostname,
                                              port=self._ssh_port,
                                              ssh_config=self._ssh_config)
    self._device.Start()

  def RunCommandPiped(self, command, **popen_kwargs):
    return self._device.RunCommandPiped(command, **popen_kwargs)

  def RunCommand(self, command, silent=False):
    return self._device.RunCommand(command, silent=silent)

  def GetFile(self, source, dest):
    self._device.GetFile(self, source, dest)

  def GetFiles(self, sources, dest):
    self._device.GetFiles(self, sources, dest)

  def ReadFile(self, target_loc):
    out, _ = self._device.RunCommandPiped(['cat', target_loc]).communicate()
    return out

  def PathExists(self, filepath):
    ret_code = self._device.RunCommand(['ls', filepath])
    return ret_code == 0

  def PutFiles(self, sources, dest):
    self._device.PutFiles(self, sources, dest)

  def IsStarted(self):
    return self._device.IsStarted()

  def IsProcessRunning(self, proc_name):
    out, _ = self._device.RunCommandPiped(
        ['ps', '|', 'grep', proc_name]).communicate()
    return proc_name in out

  def Start(self):
    self._device.Start()

  @property
  def is_local(self):
    return not self._hostname

  @property
  def hostname(self):
    return self._hostname

  @property
  def ssh_port(self):
    return self._ssh_port

  @property
  def out_dir(self):
    return self._out_dir
