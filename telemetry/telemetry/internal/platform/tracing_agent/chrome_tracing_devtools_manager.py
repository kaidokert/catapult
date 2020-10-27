# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# A singleton map from platform backends to maps of uniquely-identifying
# remote port (which may be the same as local port) to DevToolsClientBackend.
# There is no guarantee that the devtools agent is still alive.
_platform_backends_to_devtools_clients_maps = {}


def _RemoveStaleDevToolsClient(platform_backend):
  """Removes DevTools clients that are no longer connectable."""
  print('Removing stale devtools clients!')
  devtools_clients_map = _platform_backends_to_devtools_clients_maps.get(
      platform_backend, {})
  print('Map contents: %s' % str(devtools_clients_map))
  devtools_clients_map = {
      port: client
      for port, client in devtools_clients_map.iteritems()
      if client.IsAlive()
      }
  print('Map contents after checking for active: %s' % str(devtools_clients_map))
  _platform_backends_to_devtools_clients_maps[platform_backend] = (
      devtools_clients_map)


def RegisterDevToolsClient(devtools_client_backend):
  """Register DevTools client

  This should only be called from DevToolsClientBackend when it is initialized.
  """
  print('RegisterDevToolsClient registering: %s' % str(devtools_client_backend))
  remote_port = str(devtools_client_backend.remote_port)
  platform_clients = _platform_backends_to_devtools_clients_maps.setdefault(
      devtools_client_backend.platform_backend, {})
  platform_clients[remote_port] = devtools_client_backend


def GetDevToolsClients(platform_backend):
  """Get DevTools clients including the ones that are no longer connectable."""
  devtools_clients_map = _platform_backends_to_devtools_clients_maps.get(
      platform_backend, {})
  if not devtools_clients_map:
    return []
  return devtools_clients_map.values()

def GetActiveDevToolsClients(platform_backend):
  """Get DevTools clients that are still connectable."""
  _RemoveStaleDevToolsClient(platform_backend)
  return GetDevToolsClients(platform_backend)
