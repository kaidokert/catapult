# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from telemetry.internal.backends.chrome_inspector import inspector_websocket
from telemetry.internal.backends.chrome_inspector import devtools_client_backend


def GetUIDevtoolsBackend(port, app_backend, browser_target='/0'):
  client = UIDevToolsClientBackend(app_backend)
  try:
    client.Connect(port, browser_target)
    logging.info('DevTools agent ready at %s', client)
  # pylint: disable=broad-except
  except Exception as exc:
    logging.info('DevTools agent at %s not ready yet: %s', client, exc)
    client = None
  return client


class UIDevToolsClientBackend(devtools_client_backend.DevToolsClientBackend):
  def _Connect(self, port, browser_target):
    self._browser_target = browser_target or '/devtools/browser'
    self._SetUpPortForwarding(port)

    # Ensure that the inspector websocket is ready. This may raise a
    # inspector_websocket.WebSocketException or socket.error if not ready.
    self._browser_websocket = inspector_websocket.InspectorWebsocket()
    self._browser_websocket.Connect(self.browser_target_url, timeout=10)

  def SearchNodes(self, query):
    self.GetDocument()
    response = self.PerformSearch(query)
    response = self.GetSearchResults(response['result']['searchId'], 0,
                                     response['result']['resultCount'])
    return response['result']['nodeIds']

  def GetDocument(self):
    request = {
        'method': 'DOM.getDocument',
    }
    return self._browser_websocket.SyncRequest(request, timeout=60)

  def PerformSearch(self, query):
    request = {
        'method': 'DOM.performSearch',
        'params': {
            'query': query,
        }
    }
    return self._browser_websocket.SyncRequest(request, timeout=60)

  def GetSearchResults(self, search_id, from_index, to_index):
    request = {
        'method': 'DOM.getSearchResults',
        'params': {
            'searchId': search_id,
            'fromIndex': from_index,
            'toIndex': to_index,
        }
    }
    return self._browser_websocket.SyncRequest(request, timeout=60)

  # pylint: disable=redefined-builtin
  def DispatchMouseEvent(self,
                         node_id,
                         type,
                         x,
                         y,
                         button,
                         wheel_direction):
    request = {
        'method': 'DOM.dispatchMouseEvent',
        'params': {
            'nodeId': node_id,
            'event': {
                'type': type,
                'x': x,
                'y': y,
                'button': button,
                'wheelDirection': wheel_direction,
            },
        }
    }
    return self._browser_websocket.SyncRequest(request, timeout=60)
