# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import collections

# Required fields of LogEntry.
# https://chromedevtools.github.io/devtools-protocol/1-3/Log#type-LogEntry
LogEntry = collections.namedtuple('LogEntry',
                                  ['source', 'level', 'text', 'timestamp'])

class InspectorLog(object):
  def __init__(self, inspector_websocket):
    self._inspector_websocket = inspector_websocket
    self._inspector_websocket.RegisterDomain('Log', self._OnNotification)
    self._log_entries = []
    self._Enable()

  def _OnNotification(self, msg):
    if msg['method'] == 'Log.entryAdded':
      entry = msg['params']['entry']
      self._log_entries.append(
          LogEntry(entry['source'], entry['level'],
                   entry['text'], entry['timestamp']))

  def _Enable(self, timeout=10):
    self._inspector_websocket.SyncRequest({'method': 'Log.enable'}, timeout)

  def _Disable(self, timeout=10):
    self._inspector_websocket.SyncRequest({'method': 'Log.disable'}, timeout)

  def GetLogEntries(self):
    return self._log_entries
