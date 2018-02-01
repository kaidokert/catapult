# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import json

from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.common import utils
from dashboard.models import graph_data


BORING_COLUMNS = ['revision', 'timestamp']


class Timeseries2Handler(api_request_handler.ApiRequestHandler):
  def get(self, test_path):
    try:
      api_auth.AuthorizeOauthUser()
    except (api_auth.OAuthError, api_auth.NotLoggedInError):
      # If the user isn't signed in or isn't an internal user, then they won't
      # be able to access internal_only timeseries, but they should still be
      # able to access non-internal_only timeseries.
      pass

    self._SetCorsHeadersIfAppropriate()

    test_key = utils.TestKey(test_path)
    test = test_key.get()
    if not test:
      raise api_request_handler.BadRequestError(
          'Invalid test_path %s' % test_path)

    columns = self.request.get('columns')
    if not columns:
      raise api_request_handler.BadRequestError('columns required')
    columns = columns.split(',')

    min_rev = self.request.get('min_rev')
    max_rev = self.request.get('max_rev')
    if min_rev:
      min_rev = int(min_rev)
    if max_rev:
      max_rev = int(max_rev)

    q = graph_data.Row.query()
    q = q.filter(graph_data.Row.parent_test == utils.OldStyleTestKey(test_key))
    self.response.out.write(json.dumps(self._TransformRows(
        q.fetch(), min_rev, max_rev, columns)))

  @staticmethod
  def _TransformRows(entities, min_rev, max_rev, columns):
    results = []
    for entity in entities:
      if min_rev and (entity.revision < min_rev):
        continue
      if max_rev and (entity.revision > max_rev):
        continue
      row = []
      interesting = False
      for attr in columns:
        cell = getattr(entity, attr, None)
        if isinstance(cell, datetime.datetime):
          cell = cell.isoformat()
        elif isinstance(cell, float):
          cell = round(cell, 6)
        row.append(cell)
        if not interesting:
          interesting = attr not in BORING_COLUMNS and cell is not None
      if interesting:
        results.append(row)
    return results
