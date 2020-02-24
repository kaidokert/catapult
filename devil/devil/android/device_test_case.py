# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import threading
import unittest

from devil.android import device_errors
from devil.android import device_utils

_devices_lock = threading.Lock()
_devices_condition = threading.Condition(_devices_lock)
_devices = set()


def _SetUpLogging(verbosity):
  level = None
  if verbosity == 0:
    level = logging.WARNING
  elif verbosity == 1:
    level = logging.INFO
  elif verbosity >= 2:
    level = logging.DEBUG
  else:
    raise RuntimeError(
        'Logging verbosity of {} is not allowed.'.format(verbosity))
  print('verb is %s setting level to %s' % (verbosity, level))
  logging.basicConfig(
    level=level,
    format='(%(levelname)s) %(asctime)s %(module)s:%(lineno)d %(message)s')


def PrepareDevices(_, commandline_args):
  _SetUpLogging(commandline_args.verbose)

  raw_devices = device_utils.DeviceUtils.HealthyDevices()
  live_devices = []
  for d in raw_devices:
    try:
      d.WaitUntilFullyBooted(timeout=5, retries=0)
      live_devices.append(str(d))
    except (device_errors.CommandFailedError, device_errors.CommandTimeoutError,
            device_errors.DeviceUnreachableError):
      pass
  with _devices_lock:
    _devices.update(set(live_devices))

  if not _devices:
    raise Exception('No live devices attached.')

  return commandline_args


class DeviceTestCase(unittest.TestCase):
  def __init__(self, *args, **kwargs):
    super(DeviceTestCase, self).__init__(*args, **kwargs)
    self.serial = None

  #override
  def setUp(self):
    super(DeviceTestCase, self).setUp()
    with _devices_lock:
      while not _devices:
        _devices_condition.wait(5)
      self.serial = _devices.pop()

  #override
  def tearDown(self):
    super(DeviceTestCase, self).tearDown()
    with _devices_lock:
      _devices.add(self.serial)
      _devices_condition.notify()
