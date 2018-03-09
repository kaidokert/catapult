# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.common import utils
from google.appengine.api import memcache
from dashboard.models import table_config


CACHE_SECONDS = 60 * 60 * 20


class ReportNamesHandler(api_request_handler.ApiRequestHandler):

  def get(self):
    self._PreGet()
    is_internal_user = utils.IsInternalUser()
    cache_key = self._CacheKey(is_internal_user)
    cached = memcache.get(cache_key)
    if cached is not None:
      self._SetCacheControlHeader()
      self.response.write(cached)
      return

    sources = table_config.ReportTemplate.query().fetch()
    sources = [source.key.string_id() for source in sources]
    sources.sort()
    sources = json.dumps(sources)
    self._SetCacheControlHeader()
    self.response.write(sources)
    #memcache.add(cache_key, sources)

  def _PreGet(self):
    try:
      api_auth.AuthorizeOauthUser()
    except (api_auth.OAuthError, api_auth.NotLoggedInError):
      # If the user isn't signed in or isn't an internal user, then they won't
      # be able to access internal_only timeseries, but they should still be
      # able to access non-internal_only timeseries.
      pass
    self._SetCorsHeadersIfAppropriate()

  def _SetCacheControlHeader(self):
    self.response.headers['Cache-Control'] = (
        'public, max-age=%d' % CACHE_SECONDS)

  @staticmethod
  def _CacheKey(is_internal_user):
    return 'api_report_names' + ('_internal' if is_internal_user else '')
