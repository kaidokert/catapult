# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import webapp2

from dashboard.common import namespaced_stored_object


_BOTS = 'bots'


class Config(webapp2.RequestHandler):
  """Handler returning site configuration details."""

  def get(self):
    bots_to_dimensions = namespaced_stored_object.Get(_BOTS)
    self.response.out.write(json.dumps({
        'configurations': sorted(bots_to_dimensions.iterkeys()),
    }))
