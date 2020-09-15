# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import time

from telemetry.util import image_util


class InspectorBrowser(object):
  """Class that controls a browser connected by an inspector_websocket.

  This class provides utility methods for controlling a browser connected by an
  inspector_websocket. It does not perform any exception handling. All
  inspector_websocket exceptions must be handled by the caller.
  """
  def __init__(self, inspector_websocket):
    self._inspector_websocket = inspector_websocket
    self._inspector_websocket.RegisterDomain('Browser', self._OnNotification)

  def _OnNotification(self, msg):
    print(msg)

  def CloseBrowser(self, timeout=60):
    """Close the browser instance."""

    request = {
        'method': 'Browser.Close',
        }
    print(self._inspector_websocket.SyncRequest(request, timeout))
