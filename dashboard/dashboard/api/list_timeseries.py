# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import logging

from google.appengine.ext import ndb

from dashboard.api import api_request_handler
from dashboard.common import utils
from dashboard.models import graph_data


def RowToDict(row):
  d = row.to_dict(exclude=['timestamp'])
  d['parent_test'] = utils.TestPath(d['parent_test'])
  return d


class ListTimeseriesHandler2(api_request_handler.ApiRequestHandler):
  """API handler for listing timeseries for a benchmark."""

  def AuthorizedPost(self, *args):
    """Returns list in response to API requests.

    Argument:
      benchmark: name of the benchmark to list tests for

    Outputs:
      JSON list of monitored timeseries for the benchmark, see README.md.
    """
    path = self.request.get('path')
    if path:
      key = utils.TestKey(path)

      rows = graph_data.GetLatestRowsForTest(key, 3)
      logging.info(rows)
      self.response.out.write(json.dumps([RowToDict(r) for r in rows]))


class ListTimeseriesHandler(api_request_handler.ApiRequestHandler):
  """API handler for listing timeseries for a benchmark."""

  def AuthorizedPost(self, *args):
    """Returns list in response to API requests.

    Argument:
      benchmark: name of the benchmark to list tests for

    Outputs:
      JSON list of monitored timeseries for the benchmark, see README.md.
    """
    benchmark = args[0]
    only_monitored = self.request.get('only_monitored') != '0'
    query = graph_data.TestMetadata.query()
    query = query.filter(
        graph_data.TestMetadata.parent_test == utils.TestKey(benchmark))
    if only_monitored:
      sheriff_name = self.request.get('sheriff', 'Chromium Perf Sheriff')
      sheriff = ndb.Key('Sheriff', sheriff_name)
      query = query.filter(graph_data.TestMetadata.sheriff == sheriff)
    else:
      logging.info('Listing tests for %s regardless of monitoring' % benchmark)
    keys = query.fetch(keys_only=True)
    return [utils.TestPath(key) for key in keys]
