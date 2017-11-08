# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

class WindowManagerBackend(object):

  _WINDOW_MANAGER_DOMAIN = 'WindowManager'

  def __init__(self, inspector_socket):
    self._inspector_websocket = inspector_socket

  def EnterOverviewMode(self, timeout=30):
    req = {'method': self._WINDOW_MANAGER_DOMAIN + '.enterOverviewMode'}
    self._inspector_websocket.SyncRequest(req, timeout)

  def ExitOverviewMode(self, timeout=30):
    req = {'method': self._WINDOW_MANAGER_DOMAIN + '.exitOverviewMode'}
    self._inspector_websocket.SyncRequest(req, timeout)

  def Close(self):
    pass
