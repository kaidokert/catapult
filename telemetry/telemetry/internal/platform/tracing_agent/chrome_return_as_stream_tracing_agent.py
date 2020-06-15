# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import shutil

from telemetry.internal.platform.tracing_agent import chrome_tracing_agent


# A class that uses ReportEvents mode for chrome tracing.
class ChromeReturnAsStreamTracingAgent(chrome_tracing_agent.ChromeTracingAgent):
  def __init__(self, platform_backend):
    super(ChromeReturnAsStreamTracingAgent, self).__init__(platform_backend)

  def _GetTransferMode(self):
    return 'ReturnAsStream'

  def _StartStartupTracing(self, config):
    self._CreateTraceConfigFile(config)
    logging.info('Created startup trace config file in: %s',
                 self._trace_config_file)
    return True

  def _RemoveTraceConfigFile(self):
    if not self._trace_config_file:
      return
    logging.info('Remove trace config file in %s', self._trace_config_file)
    if self._platform_backend.GetOSName() == 'android':
      self._platform_backend.device.RemovePath(
          self._trace_config_file, force=True, rename=True, as_root=True)
    elif self._platform_backend.GetOSName() == 'chromeos':
      self._platform_backend.cri.RmRF(self._trace_config_file)
    elif self._platform_backend.GetOSName() in \
      chrome_tracing_agent._DESKTOP_OS_NAMES:
      if os.path.exists(self._trace_config_file):
        os.remove(self._trace_config_file)
      shutil.rmtree(os.path.dirname(self._trace_config_file))
    else:
      raise NotImplementedError
    self._trace_config_file = None

  @classmethod
  def IsSupported(cls, platform_backend):
    return platform_backend.GetOSName() != 'fuchsia'
