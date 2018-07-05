# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import platform
import subprocess
import sys

from py_utils import cloud_storage  # pylint: disable=import-error

from telemetry.internal.util import binary_manager
from telemetry.core import os_version
from telemetry.core import util
from telemetry import decorators
from telemetry.internal.platform import linux_based_platform_backend
from telemetry.internal.platform import posix_platform_backend


_POSSIBLE_PERFHOST_APPLICATIONS = [
    'perfhost_precise',
    'perfhost_trusty',
]


class LinuxPlatformBackend(
    posix_platform_backend.PosixPlatformBackend,
    linux_based_platform_backend.LinuxBasedPlatformBackend):
  def __init__(self):
    super(LinuxPlatformBackend, self).__init__()

  @classmethod
  def IsPlatformBackendForHost(cls):
    return sys.platform.startswith('linux') and not util.IsRunningOnCrosDevice()

  def IsThermallyThrottled(self):
    raise NotImplementedError()

  def HasBeenThermallyThrottled(self):
    raise NotImplementedError()

  @decorators.Cache
  def GetArchName(self):
    return platform.machine()

  def GetOSName(self):
    return 'linux'

  @decorators.Cache
  def GetOSVersionName(self):

    if os.path.exists('/etc/lsb-release'):
      codename_key_name = 'DISTRIB_CODENAME'
      release_key_name = 'DISTRIB_RELEASE'
      file_name = '/etc/lsb-release'
    elif os.path.exists('/etc/os-release'):
      codename_key_name = 'NAME'
      release_key_name = 'VERSION'
      file_name = '/etc/os-release'
    else:
      raise NotImplementedError('Unknown Linux OS version')

    codename = None
    version = None
    for line in self.GetFileContents(file_name).splitlines():
      key, _, value = line.partition('=')
      if key == codename_key_name:
        codename = value.strip()
      elif key == release_key_name:
        try:
          version = float(value)
        except ValueError:
          version = 0
      if codename and version:
        break
    return os_version.OSVersion(codename, version)

  def GetOSVersionDetailString(self):
    return ''  # TODO(kbr): Implement this.

  def CanFlushIndividualFilesFromSystemCache(self):
    return True

  def SupportFlushEntireSystemCache(self):
    return self.HasRootAccess()

  def FlushEntireSystemCache(self):
    p = subprocess.Popen(['/sbin/sysctl', '-w', 'vm.drop_caches=3'])
    p.wait()
    assert p.returncode == 0, 'Failed to flush system cache'

  def CanLaunchApplication(self, application):
    if application == 'ipfw' and not self._IsIpfwKernelModuleInstalled():
      return False
    return super(LinuxPlatformBackend, self).CanLaunchApplication(application)

  def InstallApplication(self, application):
    if application == 'ipfw':
      self._InstallIpfw()
    elif application == 'avconv':
      self._InstallBinary(application)
    elif application in _POSSIBLE_PERFHOST_APPLICATIONS:
      self._InstallBinary(application)
    else:
      raise NotImplementedError(
          'Please teach Telemetry how to install ' + application)

  def CanMonitorPower(self):
    return False

  def CanMeasurePerApplicationPower(self):
    return False

  def _IsIpfwKernelModuleInstalled(self):
    return 'ipfw_mod' in subprocess.Popen(
        ['lsmod'], stdout=subprocess.PIPE).communicate()[0]

  def _InstallIpfw(self):
    ipfw_bin = binary_manager.FindPath(
        'ipfw', self.GetArchName(), self.GetOSName())
    ipfw_mod = binary_manager.FindPath(
        'ipfw_mod.ko', self.GetArchName(), self.GetOSName())

    try:
      changed = cloud_storage.GetIfChanged(
          ipfw_bin, cloud_storage.INTERNAL_BUCKET)
      changed |= cloud_storage.GetIfChanged(
          ipfw_mod, cloud_storage.INTERNAL_BUCKET)
    except cloud_storage.CloudStorageError, e:
      logging.error(str(e))
      logging.error('You may proceed by manually building and installing'
                    'dummynet for your kernel. See: '
                    'http://info.iet.unipi.it/~luigi/dummynet/')
      sys.exit(1)

    if changed or not self.CanLaunchApplication('ipfw'):
      if not self._IsIpfwKernelModuleInstalled():
        subprocess.check_call(['/usr/bin/sudo', 'insmod', ipfw_mod])
      os.chmod(ipfw_bin, 0755)
      subprocess.check_call(
          ['/usr/bin/sudo', 'cp', ipfw_bin, '/usr/local/sbin'])

    assert self.CanLaunchApplication('ipfw'), 'Failed to install ipfw. ' \
        'ipfw provided binaries are not supported for linux kernel < 3.13. ' \
        'You may proceed by manually building and installing dummynet for ' \
        'your kernel. See: http://info.iet.unipi.it/~luigi/dummynet/'

  def _InstallBinary(self, bin_name):
    bin_path = binary_manager.FetchPath(
        bin_name, self.GetArchName(), self.GetOSName())
    os.environ['PATH'] += os.pathsep + os.path.dirname(bin_path)
    assert self.CanLaunchApplication(bin_name), 'Failed to install ' + bin_name
