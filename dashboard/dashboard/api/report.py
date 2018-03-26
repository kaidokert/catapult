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


def GetSuffixedValue(key, statistic, revision):
  test = timeseries2.FindTest(*(list(key) + [statistic, 'test']))
  if not test:
    return None
  if test.key.id().find('/' + key[1] + '_' + statistic) < 0:
    return None
  row = utils.GetRowKey(test.key, revision).get()
  if not row:
    return None
  return row.value


IMPROVEMENT_DIRECTION_SUFFIXES = {
    anomaly.UP: '_biggerIsBetter',
    anomaly.DOWN: '_smallerIsBetter',
    anomaly.UNKNOWN: '',
}

# Map from Chromium milestone revision to revisions for other bots.
REVISIONS_BY_PUBLIC_BOT = {
    'ChromiumPerf:android-nexus5X': {
        540302: 540345,
    },
}
REVISIONS_BY_INTERNAL_BOT_HASH = {
    '7482c0162be69d8cf57b15b2a16254556f9c904745cb52ff15085912c4807a06': {
        416640: 1473196450,
        423768: 1475824394,
        433391: 1475841673,
        433400: 1479536199,
        445288: 1485025126,
        447949: 1486119399,
        454466: 1488528859,
        454523: 1488538235,
        463842: 1491977185,
        465221: 1492542658,
        474839: 1495792284,
        474952: 1495802833,
        488392: 1500610872,
        488576: 1500628339,
        498621: 1504160258,
        499187: 1504294629,
        508578: 1507887190,
        520719: 1512141580,
        530282: 1516341121,
        530373: 1516353162,
        540240: 1519951206,
        540302: 1519960286,
        543346: 1521148924,
    },
    'e806409e6a617aa73361d2ae79834db91498583b437872360d0d12e8d4a168b3': {
        540240: 1519951206,
        540302: 1519972757,
        543346: 1521144266,
    },
    '8e0a42aae55af6c11c075bc2636da1d5c3f6c181d76bc253202933c5f30bca31': {
        540240: 1519951206,
        540302: 1519972757,
        543346: 1521144266,
    },
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
    if units in ['sizeInBytes', 'W']:
      units += IMPROVEMENT_DIRECTION_SUFFIXES[avg_test.improvement_direction]

    test_revision = revision
    master_bot = avg_test.master_name + ':' + avg_test.bot_name
    if master_bot in REVISIONS_BY_PUBLIC_BOT:
      rev_map = REVISIONS_BY_PUBLIC_BOT[master_bot]
      if revision in rev_map:
        test_revision = rev_map[revision]
    else:
      bot_hash = describe.Hash(master_bot)
      if bot_hash in REVISIONS_BY_INTERNAL_BOT_HASH:
        rev_map = REVISIONS_BY_INTERNAL_BOT_HASH[bot_hash]
        if revision in rev_map:
          test_revision = rev_map[revision]

    avg_row = utils.GetRowKey(avg_test.key, test_revision).get()
    logging.info('got rev=%r row=%r', revision, avg_row)
    if not avg_row:
      # query for the whole timeseries since we don't have an index with
      # revision.
      entities = graph_data.Row.query().filter(
          graph_data.Row.parent_test ==
          utils.OldStyleTestKey(avg_test.key.id())).fetch()
      if len(entities) == 0:
        logging.info('Zero Rows %r', avg_test.key.id())
        continue
      if avg_test.master_name == 'ChromiumPerf':
        entity_revisions = [entity.revision for entity in entities]
      elif entities[-1].r_commit_pos:
        entity_revisions = [int(entity.r_commit_pos) for entity in entities]
      i = bisect.bisect_left(entity_revisions, revision)
      if i == len(entities):
        i -= 1
      avg_row = entities[i]
      logging.info('found i=%d rev=%r using=%r prev=%r next=%r', i, revision,
                   avg_row, entities[i-1], entities[i+1])

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

  count = sum(counts.itervalues())
  avg = None
  std = None
  if count > 0:
    avg = sum(avgs[key] * counts[key] for key in avgs.iterkeys()) / count
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

  if math.isinf(max_value):
    max_value = None
  if math.isinf(min_value):
    min_value = None

  statistics = {
      'avg': avg,
      'count': count,
      'max': max_value,
      'min': min_value,
      'std': std,
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
      'owners': entity.owners,
      'name': entity.name,
      'url': entity.url,
      'statistics': entity.template['statistics'],
      'rows': [RenderRow(row, entity.template['statistics'], revisions)
               for row in entity.template['rows']],
  }
  return report, entity.internal_only


def TemplateHasInternalTimeseries(rows):
  suitebots = set()
  for row in rows:
    suitebots.add((tuple(row['testSuites']), tuple(row['bots'])))
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
    if not any_internal_timeseries:
      # Also delete the internal cached report names.
      memcache.delete(report_names.CacheKey(True))

  def get(self):
    self._PreGet()
    template_id = int(self.request.get('id'))
    revisions = self.request.get('revisions')
    is_internal_user = utils.IsInternalUser()
    logging.info('id=%r internal=%r email=%r revisions=%r',
                 template_id, is_internal_user, utils.GetUserEmail(), revisions)

    # Cache-Control can be set because the template modified timestamp is part
    # of the URL, even though this handler doesn't use it.
    # Memcache cannot be used because there's no way afaict to memcache.delete()
    # reports for all revisions when the ReportTemplate is updated.

    revisions = [int(revision) for revision in revisions.split(',')]
    report, private = GetReport(template_id, revisions)
    if report is None:
      self.response.set_status(404)
      self.response.write(json.dumps({'error': 'not found'}))
      return

    report = json.dumps(report)
    self._SetCacheControlHeader(private)
    self.response.write(report)

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
    self.response.headers['Cache-Control'] = '%s, max-age=%d' % (
        'private' if private else 'public', CACHE_SECONDS)
