# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import json

from dashboard import alerts
from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import graph_data
from dashboard.models import histogram


class DescribeHandler(api_request_handler.ApiRequestHandler):
  def get(self, test_suite):
    try:
      api_auth.AuthorizeOauthUser()
    except (api_auth.OAuthError, api_auth.NotLoggedInError):
      # If the user isn't signed in or isn't an internal user, then they won't
      # be able to access internal_only timeseries, but they should still be
      # able to access non-internal_only timeseries.
      pass

    self._SetCorsHeadersIfAppropriate()

    measurements = set()
    bots = set()
    test_cases = set()
    # Find all test paths that start with test_suite.
    # Strip /ref and _ref.
    # Collect all measurements, bots, test cases.
    descriptor = {
      'measurements': list(measurements),
      'bots': list(bots),
      'test_cases': list(test_cases),
    }
    self.response.write(json.dumps(descriptor))
