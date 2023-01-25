# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
import logging
import os
import shlex
import subprocess
import sys

from py_utils import cloud_storage  # pylint: disable=import-error

from telemetry.internal.util import binary_manager
from telemetry.core import os_version
from telemetry.core import linux_interface
from telemetry import decorators
from telemetry.internal.platform import linux_based_platform_backend
from telemetry.internal.platform import linux_device
from telemetry.core import platform
from telemetry.internal.forwarders import linux_based_forwarder
from telemetry.internal.platform import posix_platform_backend


_POSSIBLE_PERFHOST_APPLICATIONS = [
    'perfhost_precise',
    'perfhost_trusty',
]


def _GetOSVersion(value):
  if value == 'rodete':
    return 0.0

  try:
    return float(value)
  except (TypeError, ValueError):
    logging.error('Unrecognizable OS version: %s. Will fallback to 0.0', value)
    return 0.0


class LinuxPlatformBackend(
    posix_platform_backend.PosixPlatformBackend,
    linux_based_platform_backend.LinuxBasedPlatformBackend):

  def __init__(self, device=None):
    super().__init__()
    if device and not device.is_local:
      self._li = linux_interface.LinuxInterface(device.host_name,
                                                device.ssh_port,
                                                device.ssh_identity)
    else:
      self._li = linux_interface.LinuxInterface()

  @classmethod
  def IsPlatformBackendForHost(cls):
    # Its for the host if the device is local.
    # TODO: How to check this??
    return sys.platform.startswith('linux')

  @classmethod
  def SupportsDevice(cls, device):
    return isinstance(device, linux_device.LinuxDevice)

  @classmethod
  def CreatePlatformForDevice(cls, device, finder_options):
    del finder_options
    assert cls.SupportsDevice(device)
    return platform.Platform(LinuxPlatformBackend(device))

  def IsThermallyThrottled(self):
    raise NotImplementedError()

  def HasBeenThermallyThrottled(self):
    raise NotImplementedError()

  def _CreateForwarderFactory(self):
    logging.debug('Creating forwarder factory in LinuxPlatformBackend')
    logging.debug('Interface is local? %s', str(self.interface.local))
    return linux_based_forwarder.LinuxBasedForwarderFactory(self.interface)

  @decorators.Cache
  def GetArchName(self):
    return self.interface.GetArchName()

  @property
  def interface(self):
    return self._li

  @property
  def has_interface(self):
    return True

  def GetDisplays(self):
    return self.interface.GetDisplays()

  def GetOSName(self):
    return 'linux'

  def _ReadReleaseFile(self, file_path):
    if self.has_interface and not self._li.FileExistsOnDevice(file_path):
      return None

    release_data = {}
    for line in self.GetFileContents(file_path).splitlines():
      key, _, value = line.partition('=')
      release_data[key] = ' '.join(shlex.split(value.strip()))
    return release_data

  @decorators.Cache
  def GetOSVersionName(self):
    # First try os-release(5).
    for path in ('/etc/os-release', '/usr/lib/os-release'):
      os_release = self._ReadReleaseFile(path)
      if os_release:
        codename = os_release.get('ID', 'linux')
        version = _GetOSVersion(os_release.get('VERSION_ID'))
        return os_version.OSVersion(codename, version)

    # Use lsb-release as a fallback.
    lsb_release = self._ReadReleaseFile('/etc/lsb-release')
    if lsb_release:
      codename = lsb_release.get('DISTRIB_CODENAME')
      version = _GetOSVersion(lsb_release.get('DISTRIB_RELEASE'))
      return os_version.OSVersion(codename, version)

    raise NotImplementedError('Unknown Linux OS version')

  def GetOSVersionDetailString(self):
    # First try os-release
    for path in ('/etc/os-release', '/usr/lib/os-release'):
      os_release = self._ReadReleaseFile(path)
      if os_release:
        codename = os_release.get('NAME')
        version = os_release.get('VERSION')
        return codename + ' ' + version

    # Use lsb-release as a fallback.
    lsb_release = self._ReadReleaseFile('/etc/lsb-release')
    if lsb_release:
      return lsb_release.get('DISTRIB_DESCRIPTION')

    raise NotImplementedError('Missing Linux OS name or version')

  def CanTakeScreenshot(self):
    rc, _, _ = self._li.RunCmdOnDeviceWithRC(['which', 'gnome-screenshot'])
    return rc == 0

  def TakeScreenshot(self, file_path):
    return self._li.TakeScreenshot(file_path)

  def CanFlushIndividualFilesFromSystemCache(self):
    return True

  def SupportFlushEntireSystemCache(self):
    return self.HasRootAccess()

  def FlushEntireSystemCache(self):
    rc, _, _ = self._li.RunCmdOnDeviceWithRC(
        ['/sbin/sysctl', '-w', 'vm.drop_caches=3'])
    assert rc == 0, 'Failed to flush system cache'

  def CanLaunchApplication(self, application):
    if application == 'ipfw' and not self._IsIpfwKernelModuleInstalled():
      return False
    rc, _, _ = self._li.RunCmdOnDeviceWithRC(['which', application])
    return rc == 0

  def InstallApplication(self, application):
    if application == 'ipfw':
      self._InstallIpfw()
    elif application == 'avconv':
      self._InstallBinary(application)
    elif application in _POSSIBLE_PERFHOST_APPLICATIONS:
      self._InstallBinary(application)
    else:
      raise NotImplementedError('Please teach Telemetry how to install ' +
                                application)

  def _IsIpfwKernelModuleInstalled(self):
    stdout, _ = self._li.RunCmdOnDevice(['lsmod'])
    return 'ipfw_mod' in stdout

  def _InstallIpfw(self):
    # Only supported in local case for now.
    # TODO: I believe this is used for port-forwarding from the host.
    # Could be host-only, in that case.
    if not self._li.local:
      raise NotImplementedError
    ipfw_bin = binary_manager.FetchPath('ipfw', self.GetArchName(),
                                        self.GetOSName())
    ipfw_mod = binary_manager.FetchPath('ipfw_mod.ko', self.GetArchName(),
                                        self.GetOSName())

    try:
      changed = cloud_storage.GetIfChanged(ipfw_bin,
                                           cloud_storage.INTERNAL_BUCKET)
      changed |= cloud_storage.GetIfChanged(ipfw_mod,
                                            cloud_storage.INTERNAL_BUCKET)
    except cloud_storage.CloudStorageError as e:
      logging.error(str(e))
      logging.error('You may proceed by manually building and installing'
                    'dummynet for your kernel. See: '
                    'http://info.iet.unipi.it/~luigi/dummynet/')
      sys.exit(1)

    if changed or not self.CanLaunchApplication('ipfw'):
      if not self._IsIpfwKernelModuleInstalled():
        subprocess.check_call(['/usr/bin/sudo', 'insmod', ipfw_mod])
      os.chmod(ipfw_bin, 0o755)
      subprocess.check_call(
          ['/usr/bin/sudo', 'cp', ipfw_bin, '/usr/local/sbin'])

    assert self.CanLaunchApplication('ipfw'), 'Failed to install ipfw. ' \
        'ipfw provided binaries are not supported for linux kernel < 3.13. ' \
        'You may proceed by manually building and installing dummynet for ' \
        'your kernel. See: http://info.iet.unipi.it/~luigi/dummynet/'

  def _InstallBinary(self, bin_name):
    if not self._li.local:
      raise NotImplementedError
    bin_path = binary_manager.FetchPath(bin_name, self.GetOSName(),
                                        self.GetArchName())
    os.environ['PATH'] += os.pathsep + os.path.dirname(bin_path)
    assert self.CanLaunchApplication(bin_name), 'Failed to install ' + bin_name

  def IsRemoteDevice(self):
    return not self._li.local
