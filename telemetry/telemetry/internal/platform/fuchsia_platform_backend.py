# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from telemetry import decorators
from telemetry.core import platform
from telemetry.internal.forwarders import fuchsia_forwarder
from telemetry.internal.platform import fuchsia_device
from telemetry.internal.platform import platform_backend


class FuchsiaPlatformBackend(platform_backend.PlatformBackend):
  def __init__(self, device):
    super(FuchsiaPlatformBackend, self).__init__(device)
    self._command_runner = None

  @classmethod
  def SupportsDevice(cls, device):
    return isinstance(device, fuchsia_device.FuchsiaDevice)

  @classmethod
  def CreatePlatformForDevice(cls, device, finder_options):
    assert cls.SupportsDevice(device)
    return platform.Platform(FuchsiaPlatformBackend(device))

  def _CreateForwarderFactory(self):
    return fuchsia_forwarder.FuchsiaForwarderFactory(self._command_runner)

  def IsRemoteDevice(self):
    return True

  def IsThermallyThrottled(self):
    raise NotImplementedError()

  def HasBeenThermallyThrottled(self):
    raise NotImplementedError()

  def RunCommand(self, args):
    raise NotImplementedError()

  def StartCommand(self, args, cwd=None, quiet=False, connect_timeout=None):
    raise NotImplementedError()

  def GetFile(self, filename, destfile=None):
    raise NotImplementedError()

  def GetFileContents(self, filename):
    raise NotImplementedError()

  def PushContents(self, text, remote_filename):
    raise NotImplementedError()

  def GetDeviceTypeName(self):
    raise NotImplementedError()

  @decorators.Cache
  def GetArchName(self):
    raise NotImplementedError()

  def GetOSName(self):
    raise NotImplementedError()

  def GetOSVersionName(self):
    raise NotImplementedError()

  def GetOSVersionDetailString(self):
    raise NotImplementedError()

  def CanFlushIndividualFilesFromSystemCache(self):
    raise NotImplementedError()

  def FlushEntireSystemCache(self):
    raise NotImplementedError()

  def FlushSystemCacheForDirectory(self, directory):
    raise NotImplementedError()

  def PathExists(self, path, timeout=None, retries=None):
    raise NotImplementedError()

  def CanTakeScreenshot(self):
    raise NotImplementedError()

  def TakeScreenshot(self, file_path):
    raise NotImplementedError()

