# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import json
import logging

from google.appengine.ext import ndb

from dashboard import alerts
from dashboard.api import api_auth
from dashboard.api import describe
from dashboard.api import api_request_handler
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import graph_data
from dashboard.models import histogram


BORING_COLUMNS = ['revision', 'timestamp']


def WaitAnySuccess(futures):
  while futures:
    ndb.Future.wait_any(futures)
    new_futures = []
    for future in futures:
      if not future.done():
        new_futures.append(future)
        continue
      if future.get_exception():
        logging.info('%r', future.get_exception())
        continue
      result = future.get_result()
      if result:
        return result
    futures = new_futures


def FindTest(
    test_suite, measurement, bot, test_case, statistic, build_type):
  test_paths = [
      CompileTest(bot, test_suite, measurement, test_case),
      CompileTest(bot, test_suite, measurement + '_' + statistic, test_case),
  ]
  if build_type == 'reference':
    test_paths = [
        test_path + '_ref' for test_path in test_paths
    ] + [
        test_path + '/ref' for test_path in test_paths
    ]
  logging.info('test_paths %s', ' '.join(test_paths))
  futures = [utils.TestKey(test_path).get_async() for test_path in test_paths]
  return WaitAnySuccess(futures)


def CompileTest(bot, test_suite, measurement, test_case):
  components = bot.split(':')
  suite_name, test_part1_name = describe.ParseTestSuite(test_suite)
  components.append(suite_name)
  if test_part1_name:
    components.append(test_part1_name)
  # TODO split measurement for some internal test_suites
  components.append(measurement)
  if test_case:
    if test_suite.startswith('system_health'):
      test_case = test_case.split(':')
      components.append('_'.join(test_case[:2]))
      components.append('_'.join(test_case))
    else:
      components.append(test_case)
  return '/'.join(components)


class Timeseries2Handler(api_request_handler.ApiRequestHandler):
  def _PreGet(self):
    try:
      api_auth.AuthorizeOauthUser()
    except (api_auth.OAuthError, api_auth.NotLoggedInError):
      # If the user isn't signed in or isn't an internal user, then they won't
      # be able to access internal_only timeseries, but they should still be
      # able to access non-internal_only timeseries.
      pass
    self._SetCorsHeadersIfAppropriate()

  def get(self):
    self._PreGet()
    test_suite = self.request.get('testSuite')
    measurement = self.request.get('measurement')
    bot = self.request.get('bot')
    test_case = self.request.get('testCase')
    statistic = self.request.get('statistic')
    build_type = self.request.get('buildType')
    test = FindTest(
        test_suite, measurement, bot, test_case, statistic, build_type)

    if not test:
      self.response.set_status(404)
      self.response.write(json.dumps({'error': 'timeseries not found'}))
      return
    logging.info('found %r', test.key.id())

    columns = self.request.get('columns')
    if not columns:
      self.response.set_status(400)
      self.response.write(json.dumps({'error': 'missing "columns" parameter'}))
      return
    columns = columns.split(',')

    min_rev = self.request.get('minRevision')
    if min_rev:
      min_rev = int(min_rev)
    max_rev = self.request.get('maxRevision')
    if max_rev:
      max_rev = int(max_rev)
    min_timestamp = self.request.get('minTimestamp')
    if min_timestamp:
      min_timestamp = datetime.datetime.utcfromtimestamp(min_timestamp)
    max_timestamp = self.request.get('maxTimestamp')
    if max_timestamp:
      max_timestamp = datetime.datetime.utcfromtimestamp(max_timestamp)

    rows = graph_data.Row.query().filter(
        graph_data.Row.parent_test == utils.OldStyleTestKey(test.key.id()))
    if min_timestamp:
      rows = rows.filter(graph_data.Row.timestamp > min_timestamp)

    alert_entities = {}
    if 'alert' in columns:
      alert_entities = dict(
          (entity.end_revision, alerts.GetAnomalyDict(entity))
          for entity in anomaly.Anomaly.GetAlertsForTest(test))
    hist_entities = {}
    if 'hist' in columns:
      hist_entities = dict(
          (entity.revision, entity.data)
          for entity in histogram.Histogram.query().filter(
              histogram.Histogram.test == test.key.id()))

    self.response.out.write(json.dumps({
        'timeseries': self._TransformRows(
            rows.fetch(), columns, alert_entities, hist_entities, min_rev,
            max_rev, max_timestamp),
        'units': test.units,
    }))

  @staticmethod
  def _TransformRows(
      entities, columns, alert_entities, hist_entities, min_rev, max_rev,
      max_timestamp):
    entities = sorted(entities, key=lambda r: r.revision)
    results = []
    for entity in entities:
      if min_rev and (entity.revision < min_rev):
        continue
      if max_rev and (entity.revision > max_rev):
        continue
      if max_timestamp and (entity.timestamp > max_timestamp):
        continue

      row = []
      interesting = False
      for attr in columns:
        if attr == 'alert':
          cell = alert_entities.get(entity.revision)
        elif attr == 'hist':
          cell = hist_entities.get(entity.revision)
        else:
          cell = getattr(entity, attr, None)
          if isinstance(cell, datetime.datetime):
            cell = cell.isoformat()
          elif isinstance(cell, float):
            cell = round(cell, 6)
        row.append(cell)
        if not interesting:
          interesting = attr not in BORING_COLUMNS and cell is not None
      if interesting:
        results.append(row)
    return results
