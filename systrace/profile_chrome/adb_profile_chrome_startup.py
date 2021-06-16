# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import optparse
import os
import sys
import webbrowser

_SYSTRACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(_SYSTRACE_DIR)

from profile_chrome import chrome_startup_tracing_agent
from profile_chrome import flags
from profile_chrome import profiler
from profile_chrome import ui
from systrace import util
from systrace.tracing_agents import atrace_agent

_CATAPULT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.append(os.path.join(_CATAPULT_DIR, 'devil'))

from devil.android import device_utils
from devil.android.sdk import adb_wrapper


_CHROME_STARTUP_MODULES = [atrace_agent, chrome_startup_tracing_agent]
_DEFAULT_CHROME_CATEGORIES = '_DEFAULT_CHROME_CATEGORIES'


def _CreateOptionParser():
  parser = optparse.OptionParser(description='Record about://tracing profiles '
                                 'from Android browsers startup, combined with '
                                 'Android systrace. See http://dev.chromium.org'
                                 '/developers/how-tos/trace-event-profiling-'
                                 'tool for detailed instructions for '
                                 'profiling.', conflict_handler='resolve')
  parser = util.get_main_options(parser)

  browsers = sorted(util.get_supported_browsers().keys())
  parser.add_option('-b', '--browser', help='Select among installed browsers. '
                    'One of ' + ', '.join(browsers) + ', "stable" is used by '
                    'default.', type='choice', choices=browsers,
                    default='stable')
  parser.add_option('-v', '--verbose', help='Verbose logging.',
                    action='store_true')
  parser.add_option('-z', '--compress', help='Compress the resulting trace '
                    'with gzip. ', action='store_true')
  parser.add_option('-t', '--time', help='Stops tracing after N seconds, 0 to '
                    'manually stop (startup trace ends after at most 5s).',
                    default=5, metavar='N', type='int', dest='trace_time')
  parser.add_option('-c', '--chrome_categories', help='Chrome tracing '
                    'categories to record.', default=_DEFAULT_CHROME_CATEGORIES,
                    type='string')
  parser.add_option('-u', '--atrace-buffer-size', help='Number of bytes to'
                    ' be used for capturing atrace data', type='int',
                    default=None, dest='trace_buf_size')

  parser.add_option_group(chrome_startup_tracing_agent.add_options(parser))
  parser.add_option_group(atrace_agent.add_options(parser))
  parser.add_option_group(flags.OutputOptions(parser))

  return parser


def ProfileChrome():
  parser = _CreateOptionParser()
  options, _ = parser.parse_args()

  #Assume that at least one of options.write_json or options.trace_format
  #have defaulted values (no flag input)
  kFormatTypes = ['html', 'json', 'proto']
  if options.write_json and options.trace_format:
    raise ValueError("At most one parameter of --json or " +
                      "--trace_format should be provided")
  if not options.trace_format:
    options.trace_format = 'html' #default options.trace_format flag
    if not options.write_json:
      print("Using default format: html. Choose another format by specifying: " +
            "--format [html|json|proto] or -f [html|json|proto]")
  if options.trace_format not in kFormatTypes: #default value is 'html', not None
    raise ValueError("Format '{}' is not supported.".format(options.trace_format))


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
                                   write_json=options.write_json,
                                   trace_format=options.trace_format)
  if options.view:
    if sys.platform == 'darwin':
      os.system('/usr/bin/open %s' % os.path.abspath(result))
    else:
      webbrowser.open(result)


if __name__ == '__main__':
  sys.exit(main())
