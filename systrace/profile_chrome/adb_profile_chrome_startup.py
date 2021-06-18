# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import sys
import webbrowser

from profile_chrome import chrome_startup_tracing_agent
from profile_chrome import profiler
from profile_chrome import flags
from systrace import util
from systrace.tracing_agents import atrace_agent
from devil.android import device_utils
from devil.android.sdk import adb_wrapper

_CATAPULT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.append(os.path.join(_CATAPULT_DIR, 'devil'))

_CHROME_STARTUP_MODULES = [atrace_agent, chrome_startup_tracing_agent]


def ProfileChrome(options):
  """Interprets command line and profiles chrome on android device.

  Args:
    options: Command line flags with their specified values.
  """
  if not options.device_serial_number:
    devices = [a.GetDeviceSerial() for a in adb_wrapper.AdbWrapper.Devices()]
    if len(devices) == 0:
      raise RuntimeError('No ADB devices connected.')
    elif len(devices) >= 2:
      raise RuntimeError('Multiple devices connected, serial number required')
    options.device_serial_number = devices[0]

  if options.verbose:
    logging.getLogger().setLevel(logging.DEBUG)

  devices = device_utils.DeviceUtils.HealthyDevices()
  if len(devices) != 1:
    logging.error('Exactly 1 device must be attached.')
    return 1
  device = devices[0]
  package_info = util.get_supported_browsers()[options.browser]

  options.device = device
  options.package_info = package_info

  # Ensure compatibility between trace_format and write_json flags.
  # trace_format is preferred. write_json is supported for backward
  # compatibility reasons.
  flags.ParseFormatFlags(options)

  # TODO(washingtonp): Once Systrace uses all of the profile_chrome agents,
  # manually setting these options will no longer be necessary and should be
  # removed.
  options.ring_buffer = False
  options.trace_memory = False

  if options.atrace_categories in ['list', 'help']:
    atrace_agent.list_categories(atrace_agent.get_config(options))
    print '\n'
    return 0
  result = profiler.CaptureProfile(options,
                                   options.trace_time,
                                   _CHROME_STARTUP_MODULES,
                                   output=options.output_file,
                                   compress=options.compress,
                                   trace_format=options.trace_format)
  if options.view:
    if sys.platform == 'darwin':
      os.system('/usr/bin/open %s' % os.path.abspath(result))
    else:
      webbrowser.open(result)
