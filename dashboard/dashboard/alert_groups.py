# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from dashboard.common import request_handler


class AlertGroupsHandler(request_handler.RequestHandler):
  """Create, Update and Delete AlterGroups."""

  def get(self):
    # TODO(fancl): Implement AlertGroup update handler
    pass
