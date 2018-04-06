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


# 6 week chrome release cycle, plus a week for good measure.
CACHE_SECONDS = 60 * 60 * 24 * 7 * 7


@ndb.tasklet
def GetSuffixedValue(key, statistic, revision):
  test = yield timeseries2.FindTest(*(list(key) + [statistic, 'test']))
  if not test:
    raise ndb.Return(None)
  if test.key.id().find('/' + key[1] + '_' + statistic) < 0:
    raise ndb.Return(None)
  row = utils.GetRowKey(test.key, revision).get()
  if not row:
    raise ndb.Return(None)
  raise ndb.Return(row.value)


IMPROVEMENT_DIRECTION_SUFFIXES = {
    anomaly.UP: '_biggerIsBetter',
    anomaly.DOWN: '_smallerIsBetter',
    anomaly.UNKNOWN: '',
}


def BotRevisionIndexKey(test, revision):
  # Must include suite_name because some benchmarks are configured with the same
  # bot but different revision schemas. Fortunately, such benchmarks are not in
  # PARTIAL_TEST_SUITE_HASHES, or else we'd need to detect them and add
  # test_part1_name.
  return '%s_%s_%s_%d' % (
      test.master_name, test.bot_name, test.suite_name, revision)


# Memcache namespaces make it easier to manage just these memcache keys.
BOT_REVISION_NAMESPACE = 'bot_revision'


@ndb.tasklet
def GetRow(test, revision, probe=False):
  bot_revision_index_key = BotRevisionIndexKey(test, revision)
  bot_revision = memcache.get(bot_revision_index_key, BOT_REVISION_NAMESPACE)
  if bot_revision:
    logging.info('GetRow %r %r', bot_revision, test.key.id())
    row = yield utils.GetRowKey(test.key, bot_revision).get_async()
    raise ndb.Return(row)

  row = yield utils.GetRowKey(test.key, revision).get_async()
  if row:
    raise ndb.Return(row)

  if not probe:
    raise ndb.Return(None)

  # query for the whole timeseries since we don't have an index with
  # revision.
  logging.info('GetRow querying %r %r', revision, test.key.id())
  entities = yield graph_data.Row.query().filter(
      graph_data.Row.parent_test ==
      utils.OldStyleTestKey(test.key.id())).fetch_async()
  logging.info('GetRow bisecting %r %r', len(entities), test.key.id())
  if len(entities) == 0:
    raise ndb.Return(None)
  if test.master_name == 'ChromiumPerf':
    entity_revisions = [entity.revision for entity in entities]
  elif entities[-1].r_commit_pos:
    entity_revisions = [int(entity.r_commit_pos) for entity in entities]
  i = bisect.bisect_left(entity_revisions, revision)
  if i == len(entities):
    i -= 1
  row = entities[i]
  bot_revision = row.revision
  logging.info('found i=%d rev=%r using=%r', i, revision, row)
  memcache.set(bot_revision_index_key, bot_revision,
               namespace=BOT_REVISION_NAMESPACE)
  raise ndb.Return(row)


@ndb.tasklet
def GetStatisticsForKey(key, revision, statistics, results):
  avg_test = yield timeseries2.FindTest(*(list(key) + ['avg', 'test']))
  if not avg_test:
    raise ndb.Return()

  results['units'] = avg_test.units
  if results['units'] in ['sizeInBytes', 'W', 'ms']:
    results['units'] += IMPROVEMENT_DIRECTION_SUFFIXES[
        avg_test.improvement_direction]

  avg_row = yield GetRow(avg_test, revision)
  if not avg_row:
    raise ndb.Return()

  results['avgs'][key] = avg_row.value
  results['stds'][key] = avg_row.error
  results['max_value'] = max(results['max_value'], avg_row.value)
  results['min_value'] = min(results['min_value'], avg_row.value)

  avg_row_dict = avg_row.to_dict()
  if key[0] == 'memory.top_10_mobile':
    results['counts'][key] = 50
  else:
    results['counts'][key] = 1
  if 'd_max' in avg_row_dict:
    results['max_value'] = max(results['max_value'], avg_row_dict['d_max'])
  if 'd_min' in avg_row_dict:
    results['min_value'] = min(results['min_value'], avg_row_dict['d_min'])

  if avg_test.key.id().find('/' + key[1] + '_avg') >= 0:
    # TODO parallelize with avg_row
    count = yield GetSuffixedValue(key, 'count', avg_row.revision)
    if count is not None:
      results['counts'][key] = count

    if 'max' in statistics:
      row_max = yield GetSuffixedValue(key, 'max', avg_row.revision)
      if row_max is not None:
        results['max_value'] = max(results['max_value'], row_max)

    if 'min' in statistics:
      row_min = yield GetSuffixedValue(key, 'min', avg_row.revision)
      if row_min is not None:
        results['min_value'] = min(results['min_value'], row_min)


@ndb.tasklet
def GetStatisticsForRow(template_row, statistics, revision):
  test_cases = template_row['testCases'] or [None]
  keys = [
      (test_suite, template_row['measurement'], bot, test_case)
      for test_suite in template_row['testSuites']
      for bot in template_row['bots']
      for test_case in test_cases
  ]

  # TODO use RunningStatistics
  results = {
      'counts': {},
      'avgs': {},
      'stds': {},
      'max_value': -float('inf'),
      'min_value': float('inf'),
      'units': None,
  }
  yield [GetStatisticsForKey(key, revision, statistics, results)
         for key in keys]

  count = sum(results['counts'].itervalues())
  avg = None
  std = None
  if count > 0:
    avg = sum(results['avgs'][key] * results['counts'][key]
              for key in results['avgs'].iterkeys()) / count
    if all(results['counts'][key] > 1 for key in results['counts']):
      # Pooled standard deviation
      numerator = sum(
          (results['counts'][key] - 1) * results['stds'][key]
          for key in results['stds']
      )
      denominator = max(1, sum(
          results['counts'].itervalues()) - len(results['counts']))
      std = math.sqrt(numerator / denominator)
    else:
      std = sum(results['stds'][key]
                for key in results['stds']) / len(results['stds'])

  if math.isinf(results['max_value']):
    results['max_value'] = None
  if math.isinf(results['min_value']):
    results['min_value'] = None

  statistics = {
      'avg': avg,
      'count': count,
      'max': results['max_value'],
      'min': results['min_value'],
      'std': std,
  }
  # TODO other statistics
  template_row[revision] = statistics
  if results['units']:
    template_row['units'] = results['units']


@ndb.tasklet
def RenderRow(row, statistics, revisions):
  row = dict(row)
  futures = [GetStatisticsForRow(row, statistics, revision)
             for revision in revisions]
  yield futures
  raise ndb.Return(row)


@ndb.tasklet
def ProbeBots(rows, revisions):
  # Prime the bot_revision memcache by calling GetRow for each revision, for
  # each test with a unique BotRevisionIndexKey.
  descriptors_by_bot_suite = {}
  probe_test_case = None
  for row in rows:
    for test_suite in row['testSuites']:
      for bot in row['bots']:
        bot_suite = bot + '/' + test_suite
        if bot_suite in descriptors_by_bot_suite:
          continue
        descriptors_by_bot_suite[bot_suite] = (
            test_suite, row['measurement'], bot, probe_test_case)

  tests = yield [timeseries2.FindTest(*(list(descriptor) + ['avg', 'test']))
                 for descriptor in descriptors_by_bot_suite.itervalues()]

  yield [GetRow(test, revision, True)
         for test in tests
         for revision in revisions
         if test is not None]


@ndb.synctasklet
def GetReport(template_id, revisions):
  entity = yield ndb.Key('ReportTemplate', template_id).get_async()
  if entity is None:
    raise ndb.Return((None, True))

  yield ProbeBots(entity.template['rows'], revisions)

  rows = yield [
      RenderRow(row, entity.template['statistics'], revisions)
      for row in entity.template['rows']]
  logging.info('GetReport done %r', rows[:5])
  report = {
      'id': entity.key.id(),
      'owners': entity.owners,
      'name': entity.name,
      'url': entity.url,
      'statistics': entity.template['statistics'],
      'rows': rows,
  }
  raise ndb.Return((report, entity.internal_only))


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
      return {
          'error': 'invalid timeseries descriptors',
      }

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

    return {
        'id': entity.key.id(),
        'modified': report_names.EpochMs(entity.modified),
        'name': entity.name,
    }

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
