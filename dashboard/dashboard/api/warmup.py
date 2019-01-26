# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from dashboard.api import api_request_handler


class WarmupHandler(api_request_handler.ApiRequestHandler):
  def _CheckUser(self):
    pass

  def get(self):
    # XXX create fake data
    pass
