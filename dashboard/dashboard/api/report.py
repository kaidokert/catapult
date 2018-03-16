# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import bisect
import json
import logging
import math

from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.api import describe
from dashboard.api import report_names
from dashboard.api import timeseries2
from dashboard.common import utils
from dashboard.models import anomaly
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
  logging.info('%r %r %r %r', key, statistic, revision, test)
  if not test:
    return None
  if test.key.id().find('/' + key[1] + '_' + statistic) < 0:
    return None
  row = utils.GetRowKey(test.key, revision).get()
  logging.info('%r', row)
  if not row:
    return None
  return row.value


IMPROVEMENT_DIRECTION_SUFFIXES = {
    anomaly.UP: '_biggerIsBetter',
    anomaly.DOWN: '_smallerIsBetter',
    anomaly.UNKNOWN: '',
}


def GetStatistics(template_row, statistics, revision):
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
    if units in ['sizeInBytes']:
      units += IMPROVEMENT_DIRECTION_SUFFIXES[avg_test.improvement_direction]

    avg_row = utils.GetRowKey(avg_test.key, revision).get()
    if not avg_row:
      # query for the whole timeseries since we don't have an index with
      # revision.
      entities = graph_data.Row.query().filter(
          graph_data.Row.parent_test ==
          utils.OldStyleTestKey(avg_test.key.id())).fetch()
      i = bisect.bisect([entity.revision for entity in entities], revision)
      if i == len(entities):
        i -= 1
      avg_row = entities[i]
    logging.info('%r', avg_row)
    if not avg_row:
      continue

    avgs[key] = avg_row.value
    stds[key] = avg_row.error
    max_value = max(max_value, avg_row.value)
    min_value = min(min_value, avg_row.value)

    avg_row_dict = avg_row.to_dict()
    if key[0] == 'memory.top_10_mobile':
      counts[key] = 50
    else:
      counts[key] = 1
    if 'd_max' in avg_row_dict:
      max_value = max(max_value, avg_row_dict['d_max'])
    if 'd_min' in avg_row_dict:
      min_value = min(min_value, avg_row_dict['d_min'])

    if avg_test.key.id().find('/' + template_row['measurement'] + '_avg') >= 0:
      count = GetSuffixedValue(key, 'count', avg_row.revision)
      if count is not None:
        counts[key] = count

      if 'max' in statistics:
        row_max = GetSuffixedValue(key, 'max', avg_row.revision)
        if row_max is not None:
          max_value = max(max_value, row_max)

      if 'min' in statistics:
        row_min = GetSuffixedValue(key, 'min', avg_row.revision)
        if row_min is not None:
          min_value = min(min_value, row_min)

  if all(counts[key] > 1 for key in counts):
    # Pooled standard deviation
    numerator = sum(
        (counts[key] - 1) * stds[key]
        for key in stds
    )
    denominator = max(1, sum(counts.itervalues()) - len(counts))
    std = math.sqrt(numerator / denominator)
  else:
    std = sum(stds[key] for key in stds) / len(stds)

  count = sum(counts.itervalues())
  avg = sum(avgs[key] * counts[key] for key in avgs.iterkeys()) / count
  statistics = {
      'std': std,
      'count': count,
      'avg': avg,
      'max': max_value,
      'min': min_value,
  }
  # TODO other statistics
  return statistics, units

def RenderRow(row, statistics, revisions):
  row = dict(row)
  for revision in revisions:
    row[revision], row['units'] = GetStatistics(row, statistics, revision)
  return row


def GetReport(template_id, revisions):
  entity = ndb.Key('ReportTemplate', template_id).get()
  if entity is None:
    return None, True
  report = {
      'id': entity.key.id(),
      'name': entity.name,
      'url': entity.url,
      'statistics': entity.template['statistics'],
      'rows': [RenderRow(row, entity.template['statistics'], revisions)
               for row in entity.template['rows']],
  }
  if utils.GetUserEmail() in entity.owners:
    report['owners'] = entity.owners
  return report, entity.internal_only


def TemplateHasInternalTimeseries(rows):
  suitebots = set()
  for row in rows:
    suitebots.add((tuple(row['testSuites']), tuple(row['bots'])))
  logging.info('%r', list(suitebots))
  return any(
      describe.AnyPrivate(bots, *describe.ParseTestSuite(test_suite))
      for test_suites, bots in suitebots
      for test_suite in test_suites)


class ReportHandler(api_request_handler.ApiRequestHandler):

  def AuthorizedPost(self):
    body = json.loads(self.request.body)
    template_id = body.get('id')
    name = body['name']
    owners = body['owners']
    url = body.get('url')
    template = body['template']
    is_internal_user = utils.IsInternalUser()
    any_internal_timeseries = TemplateHasInternalTimeseries(template['rows'])

    if any_internal_timeseries and not is_internal_user:
      self.response.set_status(403)
      self.response.write(json.dumps({
          'error': 'invalid timeseries descriptors',
      }))

    entity = None
    if template_id:
      entity = ndb.Key('ReportTemplate', template_id).get()
    if entity:
      user_email = utils.GetUserEmail()
      if user_email not in entity.owners:
        self.response.set_status(403)
        self.response.write(json.dumps({
            'error': '%s is not an owner for %s' % (user_email, name),
        }))
        return
      entity.name = name
      entity.owners = owners
      entity.url = url
      entity.template = template
      entity.internal_only = any_internal_timeseries
    else:
      entity = table_config.ReportTemplate(
          name=name,
          owners=owners,
          url=body.get('url'),
          template=body['template'],
          internal_only=any_internal_timeseries)
    entity.put()

    memcache.delete(report_names.CacheKey(any_internal_timeseries))
    if any_internal_timeseries:
      memcache.delete(report_names.CacheKey(False))

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
    if report is None:
      self.response.set_status(404)
      self.response.write(json.dumps({'error': 'not found'}))
      return

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
