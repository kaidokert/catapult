# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import urllib

from google.appengine.datastore import datastore_query
from google.appengine.ext import ndb

from dashboard import alerts
from dashboard import group_report
from dashboard.api import api_request_handler
from dashboard.common import request_handler
from dashboard.common import utils
from dashboard.models import anomaly


TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M'


def _InequalityFilters(query, inequality_property,
                       min_end_revision, max_end_revision,
                       min_start_revision, max_start_revision,
                       min_timestamp, max_timestamp):
  # A query cannot have more than one inequality filter.
  # inequality_property allows users to decide which property to filter in the
  # query, which can significantly affect performance. If other inequalities are
  # specified, they will be handled by post_filters.

  # If callers set inequality_property without actually specifying a
  # corresponding inequality filter, then reset the inequality_property and
  # compute it automatically as if it were not specified.
  if inequality_property == 'start_revision':
    if min_start_revision is None and max_start_revision is None:
      inequality_property = None
  elif inequality_property == 'end_revision':
    if min_end_revision is None and max_end_revision is None:
      inequality_property = None
  elif inequality_property == 'timestamp':
    if min_timestamp is None and max_timestamp is None:
      inequality_property = None
  else:
    inequality_property = None

  if inequality_property is None:
    # Compute a default inequality_property.
    if min_start_revision or max_start_revision:
      inequality_property = 'start_revision'
    elif min_end_revision or max_end_revision:
      inequality_property = 'end_revision'
    elif min_timestamp or max_timestamp:
      inequality_property = 'timestamp'

  post_filters = []
  if not inequality_property:
    return query, post_filters

  if min_start_revision:
    min_start_revision = int(min_start_revision)
    if inequality_property == 'start_revision':
      query = query.filter(anomaly.Anomaly.start_revision >= min_start_revision)
    else:
      post_filters.append(lambda a: a.start_revision >= min_start_revision)

  if max_start_revision:
    max_start_revision = int(max_start_revision)
    if inequality_property == 'start_revision':
      query = query.filter(anomaly.Anomaly.start_revision <= max_start_revision)
    else:
      post_filters.append(lambda a: a.start_revision >= max_start_revision)

  if min_end_revision:
    min_end_revision = int(min_end_revision)
    if inequality_property == 'end_revision':
      query = query.filter(anomaly.Anomaly.end_revision >= min_end_revision)
    else:
      post_filters.append(lambda a: a.end_revision >= min_end_revision)

  if max_end_revision:
    max_end_revision = int(max_end_revision)
    if inequality_property == 'end_revision':
      query = query.filter(anomaly.Anomaly.end_revision <= max_end_revision)
    else:
      post_filters.append(lambda a: a.end_revision >= max_end_revision)

  if min_timestamp:
    min_timestamp = datetime.datetime.strptime(min_timestamp, TIMESTAMP_FORMAT)
    if inequality_property == 'timestamp':
      query = query.filter(anomaly.Anomaly.timestamp >= min_timestamp)
    else:
      post_filters.append(lambda a: a.timestamp >= min_timestamp)

  if max_timestamp:
    max_timestamp = datetime.datetime.strptime(max_timestamp, TIMESTAMP_FORMAT)
    if inequality_property == 'timestamp':
      query = query.filter(anomaly.Anomaly.timestamp <= max_timestamp)
    else:
      post_filters.append(lambda a: a.timestamp >= max_timestamp)

  return query, post_filters


def QueryAnomalies(
    test_suite_name=None, bot_name=None, bug_id=None, inequality_property=None,
    is_improvement=None, key=None, limit=100, master_name=None,
    max_end_revision=None, max_start_revision=None, max_timestamp=None,
    min_end_revision=None, min_start_revision=None, min_timestamp=None,
    recovered=None, sheriff=None, start_cursor=None, test=None):
  if key:
    return [ndb.Key(urlsafe=key).get()], None

  query = anomaly.Anomaly.query()
  if not utils.IsInternalUser():
    query = query.filter(anomaly.Anomaly.internal_only == False)
  if sheriff is not None:
    sheriff_key = ndb.Key('Sheriff', sheriff)
    sheriff_entity = sheriff_key.get()
    if not sheriff_entity or (
        sheriff_entity.internal_only and not utils.IsInternalUser()):
      raise api_request_handler.BadRequestError('Invalid sheriff %s' % sheriff)
    query = query.filter(anomaly.Anomaly.sheriff == sheriff_key)
  if is_improvement:
    query = query.filter(anomaly.Anomaly.is_improvement == (
        is_improvement == 'true'))
  if bug_id is not None:
    if bug_id == '':
      bug_id = None
    else:
      bug_id = int(bug_id)
    query = query.filter(anomaly.Anomaly.bug_id == bug_id)
  if recovered:
    query = query.filter(anomaly.Anomaly.recovered == (
        recovered == 'true'))
  if test:
    query = query.filter(anomaly.Anomaly.test.IN([
        utils.TestMetadataKey(test), utils.OldStyleTestKey(test)]))
  if master_name:
    query = query.filter(anomaly.Anomaly.master_name == master_name)
  if bot_name:
    query = query.filter(anomaly.Anomaly.bot_name == bot_name)
  if test_suite_name:
    query = query.filter(anomaly.Anomaly.benchmark_name == test_suite_name)
  # TODO measurement_name, test_case name

  query, post_filters = _InequalityFilters(
      query, inequality_property, min_end_revision, max_end_revision,
      min_start_revision, max_start_revision, min_timestamp, max_timestamp)
  query = query.order(-anomaly.Anomaly.timestamp)
  if start_cursor:
    start_cursor = datastore_query.Cursor(urlsafe=start_cursor)
  else:
    start_cursor = None

  results, next_cursor, more = query.fetch_page(
      limit, start_cursor=start_cursor)
  if post_filters:
    results = [alert for alert in results
               if all(post_filter(alert) for post_filter in post_filters)]
  if not more:
    next_cursor = None
  return results, next_cursor


class AlertsHandler(api_request_handler.ApiRequestHandler):
  """API handler for various alert requests."""

  def AuthorizedPost(self, *args):
    """Returns alert data in response to API requests.

    Possible list types:
      keys: A comma-separated list of urlsafe Anomaly keys.
      bug_id: A bug number on the Chromium issue tracker.
      rev: A revision number.

    Outputs:
      Alerts data; see README.md.
    """
    alert_list = None
    response = {}
    try:
      if len(args) == 0:
        alert_list, next_cursor = QueryAnomalies(
            bot_name=self.request.get('bot_name', None),
            bug_id=self.request.get('bug_id', None),
            inequality_property=self.request.get('inequality_property', None),
            is_improvement=self.request.get('is_improvement', None),
            key=self.request.get('key', None),
            limit=int(self.request.get('limit', 100)),
            master_name=self.request.get('master_name', None),
            max_end_revision=self.request.get('max_end_revision', None),
            max_start_revision=self.request.get('max_start_revision', None),
            max_timestamp=self.request.get('max_timestamp', None),
            min_end_revision=self.request.get('min_end_revision', None),
            min_start_revision=self.request.get('min_start_revision', None),
            min_timestamp=self.request.get('min_timestamp', None),
            recovered=self.request.get('recovered', None),
            sheriff=self.request.get('sheriff', None),
            start_cursor=self.request.get('cursor', None),
            test=self.request.get('test', None),
            test_suite_name=self.request.get('test_suite_name', None))
        if next_cursor:
          response['next_cursor'] = next_cursor.urlsafe()
      else:
        list_type = args[0]
        if list_type.startswith('bug_id'):
          bug_id = list_type.replace('bug_id/', '')
          response['DEPRECATION WARNING'] = (
              'Please use /api/alerts?bug_id=%s' % bug_id)
          alert_list = group_report.GetAlertsWithBugId(bug_id)
        elif list_type.startswith('keys'):
          keys = list_type.replace('keys/', '').split(',')
          response['DEPRECATION WARNING'] = (
              'Please use /api/alerts?key=%s' % keys[0])
          alert_list = group_report.GetAlertsForKeys(keys)
        elif list_type.startswith('rev'):
          rev = list_type.replace('rev/', '')
          response['DEPRECATION WARNING'] = (
              'Please use /api/alerts?max_end_revision=%s&min_start_revision=%s'
              % (rev, rev))
          alert_list = group_report.GetAlertsAroundRevision(rev)
        elif list_type.startswith('history'):
          try:
            days = int(list_type.replace('history/', ''))
          except ValueError:
            days = 7
          cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
          sheriff_name = self.request.get('sheriff', 'Chromium Perf Sheriff')
          sheriff_key = ndb.Key('Sheriff', sheriff_name)
          sheriff = sheriff_key.get()
          if not sheriff:
            raise api_request_handler.BadRequestError(
                'Invalid sheriff %s' % sheriff_name)
          response['DEPRECATION WARNING'] = (
              'Please use /api/alerts?min_timestamp=%s&sheriff=%s' % (
                  urllib.quote(cutoff.strftime(TIMESTAMP_FORMAT)),
                  urllib.quote(sheriff_name)))
          include_improvements = bool(self.request.get('improvements'))
          filter_for_benchmark = self.request.get('benchmark')
          query = anomaly.Anomaly.query(anomaly.Anomaly.sheriff == sheriff_key)
          query = query.filter(anomaly.Anomaly.timestamp > cutoff)
          if not include_improvements:
            query = query.filter(
                anomaly.Anomaly.is_improvement == False)
            response['DEPRECATION WARNING'] += '&is_improvement=false'
          if filter_for_benchmark:
            query = query.filter(
                anomaly.Anomaly.benchmark_name == filter_for_benchmark)
            response['DEPRECATION WARNING'] += (
                '&test_suite_name=' + filter_for_benchmark)

          query = query.order(-anomaly.Anomaly.timestamp)
          alert_list = query.fetch()
        else:
          raise api_request_handler.BadRequestError(
              'Invalid alert type %s' % list_type)
    except request_handler.InvalidInputError as e:
      raise api_request_handler.BadRequestError(e.message)

    anomaly_dicts = alerts.AnomalyDicts(
        [a for a in alert_list if a.key.kind() == 'Anomaly'])

    response['anomalies'] = anomaly_dicts

    return response
