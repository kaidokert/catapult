# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections
import contextlib
import logging

class DeduplicatingLogger(object):
  """A wrapper around logging that can deduplicate log entries.

  By default, forwards logging calls directly to the default logger. However,
  when within the scope of the DeduplicateLogs context manager, logs will be
  stored in the order they are received and logged once the scope is left, with
  duplicate entries removed.
  """
  def __init__(self):
    super(DeduplicatingLogger, self).__init__()
    # int used instead of bool to handle the possibility of nested scopes.
    self._scope_depth = 0
    self._stored_logs = collections.OrderedDict()

  def debug(self, *args):
    self._StoreOrLog(logging.DEBUG, *args)

  def info(self, *args):
    self._StoreOrLog(logging.INFO, *args)

  def warning(self, *args):
    self._StoreOrLog(logging.WARNING, *args)

  def error(self, *args):
    self._StoreOrLog(logging.ERROR, *args)

  def critical(self, *args):
    self._StoreOrLog(logging.CRITICAL, *args)

  @contextlib.contextmanager
  def DeduplicateLogs(self):
    self._scope_depth += 1
    try:
      yield
    finally:
      self._scope_depth -= 1
      if self._scope_depth == 0:
        self._DumpLogs()
        self._stored_logs.clear()

  def _StoreOrLog(self, log_level, *args):
    if self._scope_depth:
      self._stored_logs[args] = log_level
    else:
      logging.log(log_level, *args)

  def _DumpLogs(self):
    for args, log_level in self._stored_logs.iteritems():
      logging.log(log_level, *args)
