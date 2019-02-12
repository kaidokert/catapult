# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from dashboard.api import api_request_handler
from dashboard.common import bot_configurations
from dashboard.common import datastore_hooks
from dashboard.common import utils


class Config(api_request_handler.ApiRequestHandler):
  """Handler returning site configuration details."""

  def _CheckUser(self):
    pass

  def Post(self):
    print datastore_hooks.GetNamespace()
    print datastore_hooks.IsUnalteredQueryPermitted()
    print utils.IsInternalUser()
    print utils.GetEmail()
    return {'configurations': bot_configurations.List()}
