# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import platform

from telemetry.core import platform as telemetry_platform
from telemetry.core.fuchsia_interface import CommandRunner
from telemetry.internal.forwarders import fuchsia_forwarder
from telemetry.internal.platform import fuchsia_device
from telemetry.internal.platform import platform_backend


class FuchsiaPlatformBackend(platform_backend.PlatformBackend):
  def __init__(self, device):
    super(FuchsiaPlatformBackend, self).__init__(device)
    config_path = device.output_dir + '/ssh-keys/ssh_config'
    self._command_runner = CommandRunner(config_path,
                                         device.host,
                                         device.port)

  @classmethod
  def SupportsDevice(cls, device):
    return isinstance(device, fuchsia_device.FuchsiaDevice)

  @classmethod
  def CreatePlatformForDevice(cls, device, finder_options):
    assert cls.SupportsDevice(device)
    return telemetry_platform.Platform(FuchsiaPlatformBackend(device))

  @property
  def command_runner(self):
    return self._command_runner

  def _CreateForwarderFactory(self):
    return fuchsia_forwarder.FuchsiaForwarderFactory(self._command_runner)

  def IsRemoteDevice(self):
    return True

  def GetArchName(self):
    return platform.machine()

  def GetOSName(self):
    return 'fuchsia'

  def GetDeviceTypeName(self):
    pass

  def GetOSVersionName(self):
    return 'smart-display'

  def GetOSVersionDetailString(self):
    return ''

  def GetSystemTotalPhysicalMemory(self):
    pass

  def HasBeenThermallyThrottled(self):
    pass

  def IsThermallyThrottled(self):
    pass

  def InstallApplication(self, application):
    pass

  def LaunchApplication(self, application, parameters=None,
                        elevate_privilege=False):
    pass

  def PathExists(self, device_path, timeout=None, retries=None):
    pass

  def CanFlushIndividualFilesFromSystemCache(self):
    pass

  def FlushEntireSystemCache(self):
    pass

  def FlushSystemCacheForDirectory(self, directory):
    pass

  def StartActivity(self, intent, blocking):
    pass

  def CooperativelyShutdown(self, proc, app_name):
    # Suppress the 'abstract-method' lint warning.
    return False

  def SupportFlushEntireSystemCache(self):
    return False

  def StartDisplayTracing(self):
    pass

  def StopDisplayTracing(self):
    pass

  def TakeScreenshot(self, file_path):
    pass
