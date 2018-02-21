# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.common import utils
from dashboard.models import graph_data


class TestSuitesHandler(api_request_handler.ApiRequestHandler):
  def get(self):
    try:
      api_auth.AuthorizeOauthUser()
    except (api_auth.OAuthError, api_auth.NotLoggedInError):
      # If the user isn't signed in or isn't an internal user, then they won't
      # be able to access internal_only timeseries, but they should still be
      # able to access non-internal_only timeseries.
      pass
    self._SetCorsHeadersIfAppropriate()
    query = graph_data.TestMetadata.query()
    query = query.filter(graph_data.TestMetadata.parent_test == None)
    query = query.filter(graph_data.TestMetadata.has_rows == True)
    query = query.filter(graph_data.TestMetadata.deprecated == False)
    if not utils.IsInternalUser():
      query = query.filter(graph_data.TestMetadata.internal_only == False)
    keys = query.fetch(keys_only=True)
    test_suites = list(sorted(set(utils.TestSuiteName(key) for key in keys)))
    self.response.write(json.dumps(test_suites))
