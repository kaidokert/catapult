# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#pylint: disable=bad-indentation

import logging
import os
import subprocess
import time

from devil.android import decorators
from telemetry.core import platform as platform_mod
from telemetry.core import fuchsia_interface
from telemetry.internal.forwarders import fuchsia_forwarder
from telemetry.internal.platform import platform_backend
from telemetry.internal.platform.fuchsia_device import FuchsiaDevice

from fuchsia import run_package

class FuchsiaPlatformBackend(platform_backend.PlatformBackend):
  def __init__(self, device):
    """ Initalize an instance of FuchsiaPlatformBackend, from a device if
      available. Call sites need to use SupportsDevice before intialization to
      check whether this platform backend supports the device.

      Args:
        device: an instance of telemetry.internal.platform.device.Device.
    """
    if not device:
      raise ValueError('The Fuchsia platform backend requires a device target')
    if not self.SupportsDevice(device):
      raise ValueError('Unsupported device: %s' % device.name)
    # Handle erroneous values before calling the super-constructor
    super(FuchsiaPlatformBackend, self).__init__(device)
    self.target = None
    self._fi = fuchsia_interface.FuchsiaInterface(device)
    self._ff = None
    self._installed_progs = []

  @classmethod
  def CreatePlatformForDevice(cls, device, _):
    assert cls.SupportsDevice(device)
    return platform_mod.Platform(FuchsiaPlatformBackend(device))

  @classmethod
  def IsPlatformBackendForHost(cls):
    """ Returns whether this platform backend is the platform backend to be used
    for the host device which telemetry is running on."""
    return False

  def RunBrowser(self, args, outfile=None):
    command = ['run', 'content_shell'] + args
    if not outfile:
      outfile = open(os.devnull, 'w')
    task = self._fi.RunCommandPiped(command, stdout=outfile,
                                    stderr=subprocess.STDOUT)
    time.sleep(5)
    return task

  @classmethod
  def SupportsDevice(cls, device):
    """ Returns whether or not the device supports Fuchsia."""
    return isinstance(device, FuchsiaDevice)

  def DeletePath(self, path):
    self._fi.RunCommand(['rm', '-rf', path])

  def IsBrowserRunning(self):
    if not self._fi.IsStarted():
      return False
    ps_proc = self._fi.RunCommandPiped(['ps'],
                                       stdout=subprocess.PIPE,
                                       stderr=open(os.devnull, 'w'))
    running_procs = ps_proc.communicate()[0] # Just get stdout
    # If an executable named content_shell is in the output of ps, we can
    # assume that's our browser
    return "content_shell" in running_procs.decode("utf-8")

  def ReadFile(self, path_on_device):
    cat_command = ['cat', path_on_device]
    cat_proc = self._fi.RunCommandPiped(cat_command, stdout=subprocess.PIPE,
                                        stderr=open(os.devnull, 'w'))
    contents, err = cat_proc.communicate()
    ret_code = cat_proc.returncode
    if ret_code != 0:
      return 'command %s failed with code %s\nOut:\n%s\nErr:\n%s' % (
          cat_command, ret_code, contents, err)
    return contents.decode('utf-8')

  def Start(self):
    self._fi.Start()

  def GetRemotePort(self, port):
    return self._ff.GetDevicePortForHostPort(port)

  def _CreateForwarderFactory(self):
    if not self._ff:
      self._ff = fuchsia_forwarder.FuchsiaForwarderFactory(self._fi)
    return self._ff

  def IsRemoteDevice(self):
    """Check if target platform is on remote device.

    # TODO(stephanstross): Add support for fuchsia devices running in e.g. QEMU
    """
    return True

  def GetCommandLine(self, pid):
    raise NotImplementedError()

  def GetArchName(self):
    return "x64" # Currently the only one supported by FuchsiaForwarder

  def GetOSName(self):
    return "Fuchsia"

  # TODO(stephanstross): Find the appropriate decorator to cache this
  def GetOSVersionName(self):
    hash_path = os.path.abspath("./third_party/fuchsia-sdk/sdk/.hash")
    try:
      with open(hash_path, "r") as hashfile:
        contents = hashfile.read().strip()
        return contents
    except (OSError, IOError) as ex:
      logging.warn("Couldn't open the fuchsia hash file %s because of error %s",
                   hash_path, ex)

  def InstallApplication(self, app_path):
    """Install an application at the given path onto the device

    Args:
      app_path (path): The path to the .far file for the application. This path
          is always relative to the output directory for the fuchsia build, as
          reported by the FuchsiaInterface instance held by this class.
    """
    far_path = os.path.join(self._fi.out_dir, app_path)
    name = os.path.basename(far_path)
    if name in self._installed_progs:
      logging.info("Application %s is already installed", name)
      return
    #pylint: disable=protected-access
    run_package.RunPackage(
        self._fi.out_dir, self._fi._device, far_path, name, [], [], False, True)
    self._installed_progs.append(name)
    #pylint: enable=protected-access

  def LaunchApplication(self, application, elevate_privilege=False,
                        **popen_kwargs):
    if elevate_privilege:
      logging.warning("Fuchsia's backend does not support privilege elevation "
                      "currently")
    raise self._fi.RunCommandPiped(application, **popen_kwargs)

  def SetPlatform(self, platform):
    assert self._platform is None
    self._platform = platform

  def PathExists(self, path, timeout=None, retries=0):
    raise NotImplementedError()

    @decorators.WithExplicitTimeoutAndRetries(timeout, retries)
    def single_try_iteration():
      command = 'ls {}'.format(path)
      res = self._fi.RunCommand(command, silent=True)
      # Assume 'ls' has Posix semantics on fuchsia. Non-existence returns a
      # non-zero error code.
      return res == 0

    # Invoke the decorated function
    return single_try_iteration()

  def GetOSVersionDetailString(self):
    pass
