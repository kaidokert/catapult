# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os

from devil.android import decorators
from telemetry.core import platform, fuchsia_interface
from telemetry.internal.forwarders import fuchsia_forwarder
from telemetry.internal.platform import platform_backend
from telemetry.internal.platform.fuchsia_device import FuchsiaDevice


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
    self._forwarder = None
    self._fuchsia_interface = fuchsia_interface.FuchsiaInterface(device)

  @classmethod
  def CreatePlatformForDevice(cls, device, _):
    assert cls.SupportsDevice(device)
    return platform.Platform(FuchsiaPlatformBackend(device))

  @classmethod
  def IsPlatformBackendForHost(cls):
    """ Returns whether this platform backend is the platform backend to be used
    for the host device which telemetry is running on."""
    return False

  @classmethod
  def SupportsDevice(cls, device):
    """ Returns whether or not the device supports Fuchsia."""
    return isinstance(device, FuchsiaDevice)

  def RunCommand(self, command, silent=False):
    self._forwarder.RunCommand(command, silent=silent)

  def RunCommandPiped(self, command, **popen_kwargs):
    self._forwarder.RunCommandPiped(command, **popen_kwargs)

  def DeletePath(self, path):
    self.RunCommand(['rm', '-rf', path])

  def EnsureStart(self):
    self._forwarder.EnsureStart()

  def _CreateForwarderFactory(self):
    return fuchsia_forwarder.FuchsiaForwarderFactory()

  def GetRemotePort(self, port):
    return port

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
        contents = hashfile.read().trim()
        return contents
    except (OSError, IOError) as ex:
      logging.warn("Couldn't open the fuchsia hash file %s because of error %s",
                   hash_path, ex)

  def LaunchApplication(self, application, elevate_privilege=False,
                        **popen_kwargs):
    if elevate_privilege:
      logging.warning("Fuchsia's backend does not support privilege elevation "
                      "currently")
    raise self._forwarder.device.RunCommandPiped(application, popen_kwargs)

  def SetPlatform(self, platform):
    assert self._platform is None
    self._platform = platform

  def PathExists(self, path, timeout=None, retries=0):
    raise NotImplementedError()

    @decorators.WithExplicitTimeoutAndRetries(timeout, retries)
    def single_try_iteration():
      command = 'ls {}'.format(path)
      res = self._forwarder.device.RunCommand(command, silent=True)
      # Assume 'ls' has Posix semantics on fuchsia. Non-existence returns a
      # non-zero error code.
      return res == 0

    # Invoke the decorated function
    return single_try_iteration()
