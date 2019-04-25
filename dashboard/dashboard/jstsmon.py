# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from gae_ts_mon.handlers import TSMonJSHandler


METRICS = [
]


class JsTsMonHandler(TSMonJSHandler):

  def __init__(self, request=None, response=None):
    super(JsTsMonHandler, self).__init__(request, response)
    self.register_metrics(METRICS)

  def xsrf_is_valid(self, unused_body):  # pylint: disable=invalid-name
    return True
