# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from telemetry.internal.platform.tracing_agent import chrome_tracing_agent


# A class that uses ReportEvents mode for chrome tracing.
class ChromeReportEventsTracingAgent(chrome_tracing_agent.ChromeTracingAgent):
  def __init__(self, platform_backend, config):
    super(ChromeReportEventsTracingAgent, self).__init__(
        platform_backend, config)

  @classmethod
  def IsSupported(cls, platform_backend):
    #return platform_backend.GetOSName() == 'fuchsia'
    return False

  def _GetTransferMode(self):
    return 'ReturnAsStream'

  def _StartStartupTracing(self, config):
    print('########## CONFIG NOT BEING USED #########')
    #config._chrome_trace_config.SetJsonTraceFormat()
    print(config)


    del config
    # Fuchsia doesn't support starting tracing with a config file
    return False

  def _RemoveTraceConfigFile(self):
    pass
