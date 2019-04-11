# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Provides device interactions for CPU temperature monitoring."""
# pylint: disable=unused-argument

import logging

from devil.android import device_utils
from devil.utils import timeout_retry

logger = logging.getLogger(__name__)

_DEVICE_THERMAL_INFORMATION = {
    # Pixel 3
    'blueline': {
        'cpu_temps': {
            # See /sys/class/thermal/thermal_zone<number>/type for description
            # Types:
            # cpu0: cpu0-silver-step
            # cpu1: cpu1-silver-step
            # cpu2: cpu2-silver-step
            # cpu3: cpu3-silver-step
            # cpu4: cpu0-gold-step
            # cpu5: cpu1-gold-step
            # cpu6: cpu2-gold-step
            # cpu7: cpu3-gold-step
            'cpu0': '/sys/class/thermal/thermal_zone11/temp',
            'cpu1': '/sys/class/thermal/thermal_zone12/temp',
            'cpu2': '/sys/class/thermal/thermal_zone13/temp',
            'cpu3': '/sys/class/thermal/thermal_zone14/temp',
            'cpu4': '/sys/class/thermal/thermal_zone15/temp',
            'cpu5': '/sys/class/thermal/thermal_zone16/temp',
            'cpu6': '/sys/class/thermal/thermal_zone17/temp',
            'cpu7': '/sys/class/thermal/thermal_zone18/temp'
        },
        # Different device sensors use different multipliers
        # e.g. Pixel 3 35 degrees c is 35000
        'temp_multiplier': 1000
    },
    # Pixel
    'msm8996': {
        'cpu_temps': {
            # The following thermal zones tend to produce the most accurate
            # readings
            # Types:
            # cpu0: tsens_tz_sensor0
            # cpu1: tsens_tz_sensor1
            # cpu2: tsens_tz_sensor2
            # cpu3: tsens_tz_sensor3
            'cpu0': '/sys/class/thermal/thermal_zone1/temp',
            'cpu1': '/sys/class/thermal/thermal_zone2/temp',
            'cpu2': '/sys/class/thermal/thermal_zone3/temp',
            'cpu3': '/sys/class/thermal/thermal_zone4/temp'
        },
        'temp_multiplier': 10
    }
}


class CpuTemperature(object):

  def __init__(self, device):
    """BatteryUtils constructor.

      Args:
        device: A DeviceUtils instance.
      Raises:
        TypeError: If it is not passed a DeviceUtils instance.
    """
    if not isinstance(device, device_utils.DeviceUtils):
      raise TypeError('Must be initialized with DeviceUtils object.')
    self._device = device
    self._device_info = self._GetThermalDeviceInformation()

  def _GetThermalDeviceInformation(self):
    product_model = self._device.product_model
    if self._device.product_model.startswith('AOSP on '):
      product_model = self._device.product_model.replace('AOSP on ', '')
    return _DEVICE_THERMAL_INFORMATION.get(product_model)

  def IsSupported(self):
    """If the device is in _DEVICE_THERMAL_INFORMATION and the temperature files
    exist
    """
    if self._device_info is not None:
      return all(
          self._device.FileExists(f)
          for f in self._device_info['cpu_temps'].values())
    return False

  def LetCpuCoolToTemperature(self, target_temp, wait_period=30):
    """Lets device sit to give CPU time to cool down
    Implements a similar mechanism to battery_utils.LetBatteryCoolToTemperature
    Args:
      temp: maximum temperature to allow in degrees c.
      wait_period: time in seconds to wait between checking.
    """
    target_temp = target_temp * self._device_info['temp_multiplier']

    def cool_cpu():
      # Get the temperatures
      cpu_temp_paths = self._device_info['cpu_temps']
      temps = []
      for temp_path in cpu_temp_paths.values():
        temp_return = self._device.RunShellCommand(['cat', temp_path],
                                                   large_output=True,
                                                   check_return=True)
        # Output is an array of strings, only need the first line.
        temps.append(int(temp_return[0]))

      if not temps:
        logger.warning('Unable to read temperature files provided.')
        temps = [0]
      else:
        logger.info('Current Cpu temperatures: %s', str(temps)[1:-1])

      return all(t <= target_temp for t in temps)

    logger.info('Waiting for the cpu to cool down to %s',
                target_temp / self._device_info['temp_multiplier'])

    # Retry 3 times, each time waiting 30 seconds.
    # This negates most (if not all) of the noise in recorded results without
    # taking too long
    timeout_retry.WaitFor(cool_cpu, wait_period=wait_period, max_tries=3)

  def GetDeviceForTesting(self):
    return self._device

  def GetDeviceInfoForTesting(self):
    return self._device_info
