# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Finds devices that can be controlled by telemetry."""

from telemetry.internal.platform import android_device
from telemetry.internal.platform import cros_device
from telemetry.internal.platform import desktop_device

DEVICES = [
    android_device,
    cros_device,
    desktop_device,
]


def _GetDeviceFinders(options):
  supported_platforms = options.target_platforms
  if (not supported_platforms or
      options.platforms.ALL_PLATFORMS in supported_platforms):
    return DEVICES
  device_finders = []
  if any(p for p in supported_platforms
         if p not in options.platforms.REMOTE_PLATFORMS):
    device_finders.append(desktop_device)
  if options.platforms.ANDROID in supported_platforms:
    device_finders.append(android_device)
  if options.platforms.CHROMEOS in supported_platforms:
    device_finders.append(cros_device)
  return device_finders


def _GetAllAvailableDevices(options):
  """Returns a list of all available devices."""
  devices = []
  for finder in _GetDeviceFinders(options):
    devices.extend(finder.FindAllAvailableDevices(options))
  return devices


def GetDevicesMatchingOptions(options):
  """Returns a list of devices matching the options."""
  devices = []
  remote_platform_options = options.remote_platform_options
  if (not remote_platform_options.device or
      remote_platform_options.device == 'list'):
    devices = _GetAllAvailableDevices(options)
  elif remote_platform_options.device == 'android':
    devices = android_device.FindAllAvailableDevices(options)
  else:
    devices = _GetAllAvailableDevices(options)
    devices = [d for d in devices if d.guid ==
               options.remote_platform_options.device]

  devices.sort(key=lambda device: device.name)
  return devices
