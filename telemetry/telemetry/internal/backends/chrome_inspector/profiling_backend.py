# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
import json
import logging
import traceback

from telemetry.internal.backends.chrome_inspector import inspector_websocket
from telemetry.internal.backends.chrome_inspector import websocket


class ProfilingTimeoutException(Exception):
  pass


class ProfilingUnrecoverableException(Exception):
  pass


class ProfilingUnexpectedResponseException(Exception):
  pass


class ProfilingBackend(object):

  def __init__(self, inspector_socket):
    self._inspector_websocket = inspector_socket

  def DumpProfilingDataOfAllProcesses(self, timeout=120):
    """Causes all profiling data of all Chrome processes to be dumped to disk.
    """
    method = 'Profiling.dumpProfilingDataOfAllProcesses'
    request = {'method': method}
    try:
      response = self._inspector_websocket.SyncRequest(request, timeout)
    except inspector_websocket.WebSocketException as err:
      if issubclass(
          err.websocket_error_type, websocket.WebSocketTimeoutException):
        raise ProfilingTimeoutException(
            'Exception raised while sending a %s request:\n%s' %
            (method, traceback.format_exc()))
      else:
        raise ProfilingUnrecoverableException(
            'Exception raised while sending a %s request:\n%s' %
            (method, traceback.format_exc()))
      raise ProfilingUnrecoverableException(
          'Exception raised while sending a %s request:\n%s' %
          (method, traceback.format_exc()))

    if 'error' in response:
      code = response['error']['code']
      if code == inspector_websocket.InspectorWebsocket.METHOD_NOT_FOUND_CODE:
        logging.warning(
            '%s DevTools method not supported by the browser', method)
      else:
        raise ProfilingUnexpectedResponseException(
            'Inspector returned unexpected response for %s:\n%s' %
            (method, json.dumps(response, indent=2)))

  def Close(self):
    self._inspector_websocket = None
