# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import time

class Timing(object):
  def __init__(self, label):
    self._label = label
    self._wall_start = None
    self._cpu_start = None
    self.wall_seconds = 0
    self.cpu_seconds = 0

  def __enter__(self):
    self._wall_start = time.time()
    self._cpu_start = time.clock()

  def __exit__(self, *unused_args):
    self.wall_seconds = time.time() - self._wall_start
    self.cpu_seconds = time.clock() - self._cpu_start
    logging.info('%s_wall=%f', self._label, self.wall_seconds)
    logging.info('%s_cpu=%f', self._label, self.cpu_seconds)

  @classmethod
  def Decorate(cls, label):
    def Decorator(wrapped):
      def Wrapper(*a, **kw):
        with cls(label):
          return wrapped(*a, **kw)
      return Wrapper
    return Decorator
