# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import json

from dashboard import alerts
from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import graph_data
from dashboard.models import histogram


BORING_COLUMNS = ['revision', 'timestamp']


def FindTest(
    test_suite, measurement, bot, test_case, statistic, build_type):
  suffixed_measurement = measurement + '_' + statistic
  if build_type != 'test':
    return (CompileTest(test_suite, measurement, bot, test_case, [build_type])
            or CompileTest(test_suite, suffixed_measurement, bot, test_case,
                           [build_type]))
  else:
    return (CompileTest(test_suite, measurement, bot, test_case, []) or
            CompileTest(test_suite, suffixed_measurement, bot, test_case, []))


def CompileTest(
    test_suite, measurement, bot, test_case, build_type):
  test_suite_parts = test_suite.split(':')
  measurement_parts = [measurement]
  bot_parts = bot.split(':')
  test_case_parts = [test_case]
  test_path = '/'.join(
      bot_parts + test_suite_parts + measurement_parts + test_case_parts +
      build_type)
  return utils.TestKey(test_path)


class Timeseries2Handler(api_request_handler.ApiRequestHandler):
  def get(self, test_path):
    try:
      api_auth.AuthorizeOauthUser()
    except (api_auth.OAuthError, api_auth.NotLoggedInError):
      # If the user isn't signed in or isn't an internal user, then they won't
      # be able to access internal_only timeseries, but they should still be
      # able to access non-internal_only timeseries.
      pass

    self._SetCorsHeadersIfAppropriate()

    if test_path:
      test_key = utils.TestKey(test_path)
      test = test_key.get()
    else:
      test_suite = self.request.get('testSuite')
      measurement = self.request.get('measurement')
      bot = self.request.get('bot')
      test_case = self.request.get('testCase')
      statistic = self.request.get('statistic')
      build_type = self.request.get('buildType')
      test_key, test = FindTest(
          test_suite, measurement, bot, test_case, statistic, build_type)

    if not test:
      self.response.set_status(400)
      self.response.write(json.dumps({'error': 'invalid test path'}))
      return

    columns = self.request.get('columns')
    if not columns:
      self.response.set_status(400)
      self.response.write(json.dumps({'error': 'missing "columns" parameter'}))
      return
    columns = columns.split(',')

    min_rev = self.request.get('min_rev')
    if min_rev:
      min_rev = int(min_rev)
    max_rev = self.request.get('max_rev')
    if max_rev:
      max_rev = int(max_rev)
    min_timestamp = self.request.get('min_timestamp')
    if min_timestamp:
      min_timestamp = datetime.datetime.utcfromtimestamp(min_timestamp)
    max_timestamp = self.request.get('max_timestamp')
    if max_timestamp:
      max_timestamp = datetime.datetime.utcfromtimestamp(max_timestamp)

    rows = graph_data.Row.query()
    rows = rows.filter(graph_data.Row.parent_test == utils.OldStyleTestKey(test_key))
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
              histogram.Histogram.test == test_key))

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
