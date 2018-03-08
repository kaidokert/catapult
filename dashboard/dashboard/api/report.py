# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

from dashboard.api import api_auth
from dashboard.api import timeseries2
from dashboard.api import api_request_handler
from dashboard.common import utils
# from dashboard.models import graph_data
from dashboard.models import table_config
from google.appengine.api import memcache
from google.appengine.ext import ndb


def CacheKey(is_internal_user, name, min_rev, max_rev):
  key = 'api_report_%s_%d_%d' % (name, min_rev, max_rev)
  if is_internal_user:
    key += '_internal'
  return key


def GetTestDescriptors(row_descriptor):
  print row_descriptor


def GetReport(name, min_rev, max_rev):
  report_template = ndb.Key('ReportTemplate', name).get()
  rows = []
  for row in report_template.rows:
    tests = [timeseries2.FindTest(**descriptor)
             for descriptor in GetTestDescriptors(row.descriptor)]
    # Merge Rows/Histograms for each test at min_rev and max_rev
    print tests
    rows.append({
        'group': row.group,
        'label': row.label,
        min_rev: {
            # statistics
        },
        max_rev: {
            # statistics
        },
    })
  return {
      'is_owner': False,
      'title': '',
      'rows': rows,
      'template': {},
  }


class ReportHandler(api_request_handler.ApiRequestHandler):

  def AuthorizedPost(self):
    name = self.request.get('name')
    owners = self.request.get('owners')
    title = self.request.get('title')
    rows = self.request.get('rows')
    internal = self.request.get('internal')
    user_email = utils.GetUserEmail()
    is_internal_user = utils.IsInternalUser()
    if internal and not is_internal_user:
      raise Exception()
    report_template = None
    report_template = ndb.Key('ReportTemplate', name).get()
    if report_template and user_email not in report_template.owners:
      raise Exception()
    report_template = table_config.ReportTemplate(
        id=name,
        owners=owners,
        title=title,
        rows=rows,
        internal_only=internal)
    report_template.put()

  def get(self, name, min_rev, max_rev):
    self._PreGet()
    is_internal_user = utils.IsInternalUser()
    cache_key = CacheKey(is_internal_user, name, min_rev, max_rev)
    cached = memcache.get(cache_key)
    if cached is not None:
      self.response.write(cached)
      return

    report = GetReport(name, min_rev, max_rev)
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
