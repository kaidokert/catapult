# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.common import utils
from dashboard.models import graph_data


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

    benchmark = test_suite  # TODO split
    measurements = set()
    bots = set()
    test_cases = set()

    query = graph_data.TestMetadata.query()
    query = query.filter(graph_data.TestMetadata.suite_name == benchmark)
    query = query.filter(graph_data.TestMetadata.has_rows == True)
    query = query.filter(graph_data.TestMetadata.deprecated == False)
    for key in query.fetch(keys_only=True):
      test_path = utils.TestPath(key)
      if test_path.endswith('_ref') or test_path.endswith('/ref'):
        test_path = test_path[:-4]
      test_path = test_path.split('/')
      bot = test_path[0] + ':' + test_path[1]
      bots.add(bot)
      # Collect all measurements, bots, test cases.

    descriptor = {
        'measurements': list(measurements),
        'bots': list(bots),
        'test_cases': list(test_cases),
    }
    self.response.write(json.dumps(descriptor))
