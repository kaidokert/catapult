# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import hashlib
import json
import logging

from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.common import utils
from dashboard.models import graph_data
from google.appengine.api import memcache


def _CacheKey(is_internal_user):
  return 'api_test_suites' + ('_internal' if is_internal_user else '')


def _Hash(s):
  return hashlib.sha256(bytes(s)).hexdigest()


PARTIAL_TEST_SUITE_HASHES = [
    '147e82faca64a021f4af180c2acbeaa8be6a43478105110702869e353cda8c46',
]


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
    is_internal_user = utils.IsInternalUser()
    cache_key = _CacheKey(is_internal_user)
    cached = memcache.get(cache_key)
    if cached is not None:
      self.response.write(cached)
      return
    query = graph_data.TestMetadata.query()
    query = query.filter(graph_data.TestMetadata.parent_test == None)
    query = query.filter(graph_data.TestMetadata.deprecated == False)
    test_suites = set()
    if is_internal_user:
      public = memcache.get(_CacheKey(False))
      if public is not None:
        for test_suite in json.loads(public):
          test_suites.add(test_suite)
        query = query.filter(graph_data.TestMetadata.internal_only == True)
    else:
      query = query.filter(graph_data.TestMetadata.internal_only == False)
    keys = query.fetch(keys_only=True)
    for key in keys:
      test_suite = utils.TestSuiteName(key)
      if test_suite.startswith('video_'):
        test_suite = 'video:' + test_suite[6:]
      elif test_suite.startswith('v8.'):
        test_suite = 'v8:' + test_suite[3:]
      elif test_suite.startswith('thread_times.'):
        test_suite = 'thread_times:' + test_suite[13:]
      elif test_suite.startswith('smoothness.'):
        test_suite = 'smoothness:' + test_suite[11:]
      elif test_suite.startswith('resource_sizes '):
        test_suite = 'resource_sizes:' + test_suite[16:-1]
      elif test_suite.startswith('graphics_'):
        test_suite = 'graphics:' + test_suite[9:]
      elif test_suite.startswith('cheets_'):
        test_suite = 'cheets:' + test_suite[7:]
      elif test_suite.startswith('blink_perf.'):
        test_suite = 'blink_perf:' + test_suite[11:]
      elif test_suite.startswith('autoupdate_'):
        test_suite = 'autoupdate:' + test_suite[11:]
      elif test_suite.startswith('xr.'):
        test_suite = 'xr:' + test_suite[3:]
      if _Hash(test_suite) not in PARTIAL_TEST_SUITE_HASHES:
        test_suites.add(test_suite)
        continue
      subquery = graph_data.TestMetadata.query()
      subquery = subquery.filter(graph_data.TestMetadata.parent_test == key)
      subquery = subquery.filter(graph_data.TestMetadata.deprecated == False)
      subkeys = subquery.fetch(keys_only=True)
      for subkey in subkeys:
        subtest_suite = test_suite + ':' + subkey.id().split('/')[3]
        test_suites.add(subtest_suite)
    test_suites = list(sorted(test_suites))
    test_suites = json.dumps(test_suites)
    self.response.write(test_suites)
    memcache.add(cache_key, test_suites, time=60*60*24)
