# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import json
import logging
import os
from telemetry.internal.platform.tracing_agent import chrome_tracing_agent

from py_utils import atexit_with_log


# A class that uses ReportEvents mode for chrome tracing.
class ChromeReportEventsTracingAgent(chrome_tracing_agent.ChromeTracingAgent):
  _CHROME_TRACE_CONFIG_DIR = '/tmp/'
  _CHROME_TRACE_CONFIG_FILE_NAME = 'chrome-trace-config.json'

  def __init__(self, platform_backend, config):
    super(ChromeReportEventsTracingAgent, self).__init__(
        platform_backend, config)

  @classmethod
  def IsSupported(cls, platform_backend):
    return platform_backend.GetOSName() == 'fuchsia'

  def _GetTransferMode(self):
    return 'ReportEvents'

  def _StartStartupTracing(self, config):
    # self._CreateTraceConfigFile(config)
    # logging.info('Created startup trace config file in: %s',
    #              self._trace_config_file)
    return False

  def _CreateTraceConfigFileString(self, config):
    # See src/components/tracing/trace_config_file.h for the format
    result = {
        'trace_config':
        config.chrome_trace_config.GetChromeTraceConfigForStartupTracing()
    }
    return json.dumps(result, sort_keys=True)

  def _CreateTraceConfigFile(self, config):
    assert not self._trace_config_file
    self._trace_config_file = os.path.join(self._CHROME_TRACE_CONFIG_DIR,
                                           self._CHROME_TRACE_CONFIG_FILE_NAME)

    with open(self._CHROME_TRACE_CONFIG_FILE_NAME, 'w') as f:
      f.write(self._CreateTraceConfigFileString(config))
    self._platform_backend.WriteFile(
          self._trace_config_file,
          self._CreateTraceConfigFileString(config))
    #atexit_with_log.Register(self._RemoveTraceConfigFile)

  def _RemoveTraceConfigFile(self):
    if not self._trace_config_file:
      return
    # self._platform_backend.RemovePath(self._trace_config_file)
    # self._trace_config_file = None

