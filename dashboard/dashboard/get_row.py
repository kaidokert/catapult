# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""URL endpoint for getting a histogram."""

import json

from google.appengine.ext import ndb

from dashboard import post_data_handler
from dashboard.models import graph_data


class GetRowHandler(post_data_handler.PostDataHandler):
  """URL endpoint to get histogramby guid."""

  def post(self):
    """Fetches a histogram by guid.

    Request parameters:
      guid: GUID of requested histogram.

    Outputs:
      JSON serialized Histogram.
    """
    path = self.request.get('path')
    key = utils.TestKey(path)

    rows = graph_data.GetLatestRowsForTest(key, 3)
    self.response.out.write(json.dumps([r.to_dict() for r in rows]))
