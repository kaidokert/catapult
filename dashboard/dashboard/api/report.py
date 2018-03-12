# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import math
import re

from dashboard.api import api_auth
from dashboard.api import timeseries2
from dashboard.api import api_request_handler
from dashboard.common import utils
from dashboard.models import table_config
from google.appengine.api import memcache
from google.appengine.ext import ndb


CACHE_SECONDS = 60 * 60 * 20


def CacheKey(is_internal_user, name, revisions):
  key = 'api_report_%s_%s' % (name, revisions)
  if is_internal_user:
    key += '_internal'
  return key


def BuildStatistics(template_row, revision):
  test_cases = template_row['testCases'] or [None]
  keys = [
      (test_suite, template_row['measurement'], bot, test_case)
      for test_suite in template_row['testSuites']
      for bot in template_row['bots']
      for test_case in test_cases
  ]

  # TODO use RunningStatistics
  counts = {}
  avgs = {}
  stds = {}
  max_value = -float('inf')
  min_value = float('inf')
  for key in keys:
    count_test = timeseries2.FindTest(*(list(key) + ['count', 'test']))
    count_row = utils.GetRowKey(count_test.key, revision).get()
    if not count_row:
      counts[key] = 1
    else:
      if re.search('_count($|/)', count_test.key.id()):
        counts[key] = count_row.value
      elif count_row.d_count is not None:
        counts[key] = count_row.d_count
      else:
        counts[key] = 1

    avg_test = timeseries2.FindTest(*(list(key) + ['avg', 'test']))
    avg_row = utils.GetRowKey(avg_test.key, revision).get()
    if avg_row:
      avgs[key] = avg_row.value

    std_test = timeseries2.FindTest(*(list(key) + ['std', 'test']))
    std_row = utils.GetRowKey(std_test.key, revision).get()
    if std_row:
      if re.search('_std($|/)', std_test.key.id()):
        stds[key] = std_row.value
      elif std_row.d_std is not None:
        stds[key] = std_row.d_std
      else:
        stds[key] = std_row.error
    else:
      stds[key] = 0

    if 'max' in template_row['statistics']:
      max_test = timeseries2.FindTest(*(list(key) + ['max', 'test']))
      max_row = utils.GetRowKey(max_test, revision).get()
      if max_row:
        if re.search('_max($|/)', max_test.key.id()):
          max_value = max(max_value, max_row.value)
        elif max_row.d_max is not None:
          max_value = max(max_value, max_row.d_max)
        else:
          # This is a TBM1 row, there is no max!
          # NOTE avg_row, not max_row!
          max_value = max(max_value, avg_row.value)

    if 'min' in template_row['statistics']:
      min_test = timeseries2.FindTest(*(list(key) + ['min', 'test']))
      min_row = utils.GetRowKey(min_test, revision).get()
      if min_row:
        if re.search('_min($|/)', min_test.key.id()):
          min_value = min(min_value, min_row.value)
        elif min_row.d_min is not None:
          min_value = min(min_value, min_row.d_min)
        else:
          # This is a TBM1 row, there is no min!
          # NOTE avg_row, not min_row!
          min_value = min(min_value, avg_row.value)

  statistics = {}
  if 'count' in template_row['statistics']:
    statistics['count'] = sum(counts.itervalues())
  if 'avg' in template_row['statistics']:
    statistics['avg'] = sum(
        avgs[key] * counts[key]
        for key in avgs.iterkeys()) / (len(avgs) or 1)
  if 'std' in template_row['statistics']:
    # Pooled standard deviation
    numerator = sum(
        (counts[key] - 1) * stds[key]
        for key in stds
    )
    denominator = max(1, sum(counts.itervalues()) - len(counts))
    statistics['std'] = math.sqrt(numerator / denominator)
  if 'max' in template_row['statistics']:
    statistics['max'] = max_value
  if 'min' in template_row['statistics']:
    statistics['min'] = min_value
  # TODO support other statistics
  return statistics


def GetReport(name, revisions):
  report_template = ndb.Key('ReportTemplate', name).get()

  # Prefetch all TestMetadata keys and Row entities without worrying about their
  # place in the report, and rely on appengine to catch them in memory for the
  # synchronous fetches in BuildStatistics().
  # TODO Use tasklets.
  # See ChartTimeseries.createFetchDescriptors()
  tests = [
      timeseries2.FindTest(
          test_suite, template_row['measurement'], bot, test_case, statistic,
          'test')
      for template_row in report_template.rows
      for test_suite in template_row['testSuites']
      for bot in template_row['bots']
      for statistic in set(template_row['statistics'] + ['count', 'avg'])
      for test_case in template_row['testCases'] or [None]
  ]
  ndb.Future.wait_all([
      utils.GetRowKey(test.key, revision).get_async()
      for test in tests for revision in revisions
  ])

  report = {
      'url': report_template.url,
      'rows': [
          dict(((revision, BuildStatistics(row, revision))
                for revision in revisions), label=row['label'])
          for row in report_template.rows
      ],
  }
  if utils.GetUserEmail() in report_template.owners:
    report['template'] = {
        'owners': report_template.owners,
        'rows': report_template.rows,
    }

  return report, report_template.internal_only


class ReportHandler(api_request_handler.ApiRequestHandler):

  def AuthorizedPost(self):
    template = json.loads(self.request.body)
    name = template['name']
    owners = template['owners']
    internal = any(owner.endswith('@google.com') for owner in owners)
    user_email = utils.GetUserEmail()
    is_internal_user = utils.IsInternalUser()
    if internal and not is_internal_user:
      raise Exception()
    report_template = ndb.Key('ReportTemplate', name).get()
    if report_template and user_email not in report_template.owners:
      raise Exception()
    report_template = table_config.ReportTemplate(
        id=name,
        owners=owners,
        url=template.get('url'),
        rows=template['rows'],
        internal_only=internal)
    report_template.put()

  def get(self):
    self._PreGet()
    name = self.request.get('name')
    revisions = self.request.get('revisions')
    is_internal_user = utils.IsInternalUser()
    cache_key = CacheKey(is_internal_user, name, revisions)
    cached = memcache.get(cache_key)
    if cached is not None:
      #self._SetCacheControlHeader(True)
      self.response.write(cached)
      return

    report, unused_private = GetReport(name, revisions.split(','))
    report = json.dumps(report)
    #self._SetCacheControlHeader(private)
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

  def _SetCacheControlHeader(self, private):
    self.response.headers['Cache-Control'] = (
        'private' if private else 'public', CACHE_SECONDS)
