# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import logging
import math

from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.api import describe
from dashboard.api import report_names
from dashboard.api import timeseries2
from dashboard.common import utils
from dashboard.models import graph_data
from dashboard.models import table_config
from google.appengine.api import memcache
from google.appengine.ext import ndb


CACHE_SECONDS = 60 * 60 * 20


def CacheKey(is_internal_user, name, revisions):
  key = 'api_report_%s_%s' % (name, revisions)
  if is_internal_user:
    key += '_internal'
  return key


def GetSuffixedValue(key, statistic, revision):
  test = timeseries2.FindTest(*(list(key) + [statistic, 'test']))
  if test.key.id().find('/' + key[1] + '_' + statistic) < 0:
    return None
  row = utils.GetRowKey(test.key, revision).get()
  if not row:
    return None
  return row.value


def GetStatistics(template_row, revision):
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
  units = None
  for key in keys:
    avg_test = timeseries2.FindTest(*(list(key) + ['avg', 'test']))
    if not avg_test:
      continue

    units = avg_test.units

    avg_row = utils.GetRowKey(avg_test.key, revision).get()
    if not avg_row:
      # query for the whole timeseries since we don't have an index with
      # revision, and find the one Row closest to revision.
      entities = graph_data.Row.query().filter(
          graph_data.Row.parent_test ==
          utils.OldStyleTestKey(avg_test.key.id())).fetch()
      closest = float('inf')
      for entity in entities:
        if abs(revision - entity.revision) < abs(revision - closest):
          avg_row = entity
          closest = entity.revision
    if not avg_row:
      continue

    avg_row_dict = avg_row.to_dict()
    avgs[key] = avg_row.value
    if 'max' in template_row['statistics']:
      max_value = max(max_value, avg_row.value)
    if 'min' in template_row['statistics']:
      min_value = min(min_value, avg_row.value)

    if 'd_std' in avg_row_dict:
      stds[key] = avg_row_dict['d_std']
    else:
      stds[key] = avg_row.error

    if 'd_count' in avg_row_dict:
      counts[key] = avg_row_dict['d_count']
    else:
      counts[key] = 1

    if 'd_max' in avg_row_dict:
      max_value = max(max_value, avg_row_dict['d_max'])
    if 'd_min' in avg_row_dict:
      min_value = min(min_value, avg_row_dict['d_min'])

    if avg_test.key.id().find('/' + template_row['measurement'] + '_avg') >= 0:
      std = GetSuffixedValue(key, 'std', avg_row.revision)
      if std is not None:
        stds[key] = std

      count = GetSuffixedValue(key, 'count', avg_row.revision)
      if count is not None:
        counts[key] = count

      if 'max' in template_row['statistics']:
        max_value = max(max_value, GetSuffixedValue(
            key, 'max', avg_row.revision))

      if 'min' in template_row['statistics']:
        min_value = min(min_value, GetSuffixedValue(
            key, 'min', avg_row.revision))

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
  return statistics, units

def RenderRow(row, revisions):
  rendered = {'label': row['label']}
  for revision in revisions:
    statistics, units = GetStatistics(row, revision)
    rendered[revision] = statistics
    rendered['units'] = units
  return rendered


def GetReport(name, revisions):
  report_template = ndb.Key('ReportTemplate', name).get()
  report = {
      'url': report_template.url,
      'rows': [RenderRow(row, revisions) for row in report_template.rows],
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
    suitebots = set()
    for row in template['rows']:
      suitebots.add((tuple(row['testSuites']), tuple(row['bots'])))
    logging.info('%r', list(suitebots))
    internal = any(
        describe.AnyPrivate(bots, *describe.ParseTestSuite(test_suite))
        for test_suites, bots in suitebots
        for test_suite in test_suites)
    user_email = utils.GetUserEmail()
    is_internal_user = utils.IsInternalUser()
    if internal and not is_internal_user:
      self.response.set_status(403)
      self.response.write(json.dumps({
          'error': 'the report references internal timeseries but ' +
                   user_email + ' is not an internal user',
      }))
    report_template = ndb.Key('ReportTemplate', name).get()
    if not report_template:
      # This is a new report, so clear the report_names from memcache.
      memcache.delete(report_names.CacheKey(internal))
      if internal:
        memcache.delete(report_names.CacheKey(False))
    elif user_email not in report_template.owners:
      self.response.set_status(403)
      self.response.write(json.dumps({
          'error': '%s is not an owner for %s' % (user_email, name),
      }))
      return
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
    # TODO remove is_internal_user from CacheKey by getting the ReportTemplate
    # and checking its internal_only first.
    cache_key = CacheKey(is_internal_user, name, revisions)
    logging.info('ck:%r, i:%r, ue:%r', cache_key, is_internal_user,
                 utils.GetUserEmail())
    cached = memcache.get(cache_key)
    if cached is not None:
      # TODO uncomment _SetCacheControlHeaders when report edits slow
      # self._SetCacheControlHeader(True)
      self.response.write(cached)
      return

    revisions = [int(revision) for revision in revisions.split(',')]
    report, unused_private = GetReport(name, revisions)
    report = json.dumps(report)
    # TODO uncomment _SetCacheControlHeaders when report edits slow
    # self._SetCacheControlHeader(private)
    self.response.write(report)
    # TODO uncomment when AuthorizedPost can delete this report from memcache
    # for all revisions
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
