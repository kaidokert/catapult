# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.common import utils
from google.appengine.api import memcache


CLANK_MILESTONES = {
    54: (1473196450, 1475824394),
    55: (1475841673, 1479536199),
    56: (1479546161, 1485025126),
    57: (1486119399, 1488528859),
    58: (1488538235, 1491977185),
    59: (1492542658, 1495792284),
    60: (1495802833, 1500610872),
    61: (1500628339, 1504160258),
    62: (1504294629, 1507887190),
    63: (1507887190, None),
}


CHROMIUM_MILESTONES = {
    54: (416640, 423768),
    55: (433391, 433400),
    56: (433400, 445288),
    57: (447949, 454466),
    58: (454523, 463842),
    59: (465221, 474839),
    60: (474952, 488392),
    61: (488576, 498621),
    62: (499187, 508578),
    63: (508578, None),
}


class ReleasingReportHandler(api_request_handler.ApiRequestHandler):

  def get(self, source):
    self._PreGet()
    is_internal_user = utils.IsInternalUser()
    cache_key = self._CacheKey(is_internal_user, source)
    cached = memcache.get(cache_key)
    if cached is not None:
      self.response.write(cached)
      return

    report = {}
    report = json.dumps(report)
    self.response.write(report)
    #memcache.add(cache_key, report)

  def _PreGet(self):
    try:
      api_auth.AuthorizeOauthUser()
    except (api_auth.OAuthError, api_auth.NotLoggedInError):
      # If the user isn't signed in or isn't an internal user, then they won't
      # be able to access internal_only timeseries, but they should still be
      # able to access non-internal_only timeseries.
      pass
    self._SetCorsHeadersIfAppropriate()

  @staticmethod
  def _CacheKey(is_internal_user, source):
    key = 'api_releasing_report_' + source
    if is_internal_user:
      key += '_internal'
    return key
