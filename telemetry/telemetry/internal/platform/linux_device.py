# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import absolute_import

from telemetry.internal.platform import linux_based_device


class LinuxDevice(linux_based_device.LinuxBasedDevice):
  pass

def IsRunningOnLinux():
  return LinuxDevice.PlatformIsRunningOS()


def FindAllAvailableDevices(options):
  return LinuxDevice.FindAllAvailableDevices(options)
