# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import logging

from devil.android import decorators
from telemetry.core import platform
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
    super(FuchsiaPlatformBackend, self).__init__(device)
    if device and not self.SupportsDevice(device):
      raise ValueError('Unsupported device: %s' % device.name)
    self.target = None
    self._forwarder = None
    self.InitPlatformBackend()

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
    return "Zircon"

  def GetOSVersionName(self):
    return "Like, v0.1.0 or something. It's in alpha"

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
    """Tests whether the given path exists on the target platform. Utilizes
    devil.android.decorators to handle timeout and retry logic

    Args:
      path: path in request.
      timeout: timeout in seconds, defaults to no timeout
      retries: num of retries.
    Return:
      Whether the path exists on the target platform.
    """

    @decorators.WithExplicitTimeoutAndRetries(timeout, retries)
    def single_try_iteration():
      command = 'ls {}'.format(path)
      res = self._forwarder.device.RunCommand(command, silent=True)
      # Assume 'ls' has the same semantics as on Linux. Non-existence returns a
      # non-zero error code.
      return res == 0

    # Invoke the decorated function
    return single_try_iteration()
