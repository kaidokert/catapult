# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import datetime

from google.appengine.datastore import datastore_query
from google.appengine.ext import ndb

from dashboard import alerts
from dashboard import group_report
from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.common import request_handler
from dashboard.models import anomaly


class AlertsHandler(api_request_handler.ApiRequestHandler):
  """API handler for various alert requests."""

  def get(self):
    benchmark_name = self.request.get('benchmark_name')
    bot_name = self.request.get('bot_name')
    bug_id = self.request.get('bug_id')
    inequality_property = self.request.get('inequality_property')
    is_improvement = self.request.get('is_improvement')
    limit = int(self.request.get('limit', 100))
    master_name = self.request.get('master_name')
    max_end_revision = self.request.get('max_end_revision')
    max_start_revision = self.request.get('max_start_revision')
    max_timestamp = self.request.get('max_timestamp')
    min_end_revision = self.request.get('min_end_revision')
    min_start_revision = self.request.get('min_start_revision')
    min_timestamp = self.request.get('min_timestamp')
    recovered = self.request.get('recovered')
    sheriff = self.request.get('sheriff')
    start_cursor = self.request.get('cursor')
    test = self.request.get('test')

    try:
      api_auth.AuthorizeOauthUser()
    except (api_auth.OAuthError, api_auth.NotLoggedInError):
      # If the user isn't signed in or isn't an internal user, then they won't
      # be able to access internal_only timeseries, but they should still be
      # able to access non-internal_only timeseries.
      pass
    self._SetCorsHeadersIfAppropriate()

    query = anomaly.Anomaly.query()
    if not utils.IsInternalUser():
      query = query.filter(anomaly.Anomaly.internal_only == False)
    if sheriff is not None:
      query = query.filter(anomaly.Anomaly.sheriff == sheriff)
    if is_improvement:
      query = query.filter(anomaly.Anomaly.is_improvement == (
        is_improvement == 'true'))
    if bug_id is not None:
      if bug_id == '':
        bug_id = None
      query = query.filter(anomaly.Anomaly.bug_id == bug_id)
    if recovered:
      query = query.filter(anomaly.Anomaly.recovered == (
        recovered == 'true'))
    if test:
      query = query.filter(anomaly.Anomaly.test == test)
    if master_name:
      query = query.filter(anomaly.Anomaly.master_name == master_name)
    if bot_name:
      query = query.filter(anomaly.Anomaly.bot_name == bot_name)
    if benchmark_name:
      query = query.filter(anomaly.Anomaly.benchmark_name == benchmark_name)

    # A query cannot have more than one inequality filter.
    # inequality_property allows users to decide which property to filter in the
    # query. If other inequalities are specified, they will be handled by
    # _PostFilter.

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

    # Callers can set the inequality filters without specifying
    # inequality_property. Compute a default inequality_property.
    if inequality_property is None:
      if min_start_revision or max_start_revision:
        inequality_property = 'start_revision'
      elif min_end_revision or max_end_revision:
        inequality_property = 'end_revision'
      elif min_timestamp or max_timestamp:
        inequality_property = 'timestamp'

    if inequality_property == 'start_revision':
      if min_start_revision:
        query = query.filter(anomaly.Anomaly.start_revision >=
            int(min_start_revision))
      if max_start_revision:
        query = query.filter(anomaly.Anomaly.start_revision <=
            int(max_start_revision))
    elif inequality_property == 'end_revision':
      if min_end_revision:
        query = query.filter(anomaly.Anomaly.end_revision >=
            int(min_end_revision))
      if max_end_revision:
        query = query.filter(anomaly.Anomaly.end_revision <=
            int(max_end_revision))
    elif inequality_property == 'timestamp':
      if min_timestamp:
        query = query.filter(anomaly.Anomaly.timestamp >= int(min_timestamp))
      if max_timestamp:
        query = query.filter(anomaly.Anomaly.timestamp <= int(max_timestamp))

    def _PostFilter(alert):

    if start_cursor:
      start_cursor = datastore_query.Cursor(urlsafe=start_cursor)

    query = query.order(-anomaly.Anomaly.timestamp)

    results, next_cursor, more = query.fetch_page(
        limit, start_cursor=start_cursor)
    results = [alert for alert in results if _PostFilter(alert)]
    response = {'anomalies': alerts.AnomalyDicts(results)}
    if more and next_cursor:
      response['next_cursor'] = next_cursor.urlsafe()
    self.response.out.write(json.dumps(response))

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
    list_type = args[0]
    try:
      if list_type.startswith('bug_id'):
        bug_id = list_type.replace('bug_id/', '')
        alert_list = group_report.GetAlertsWithBugId(bug_id)
      elif list_type.startswith('keys'):
        keys = list_type.replace('keys/', '').split(',')
        alert_list = group_report.GetAlertsForKeys(keys)
      elif list_type.startswith('rev'):
        rev = list_type.replace('rev/', '')
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
        include_improvements = bool(self.request.get('improvements'))
        filter_for_benchmark = self.request.get('benchmark')
        query = anomaly.Anomaly.query(anomaly.Anomaly.sheriff == sheriff_key)
        query = query.filter(anomaly.Anomaly.timestamp > cutoff)
        if not include_improvements:
          query = query.filter(
              anomaly.Anomaly.is_improvement == False)
        if filter_for_benchmark:
          query = query.filter(
              anomaly.Anomaly.benchmark_name == filter_for_benchmark)

        query = query.order(-anomaly.Anomaly.timestamp)
        alert_list = query.fetch()
      else:
        raise api_request_handler.BadRequestError(
            'Invalid alert type %s' % list_type)
    except request_handler.InvalidInputError as e:
      raise api_request_handler.BadRequestError(e.message)

    anomaly_dicts = alerts.AnomalyDicts(
        [a for a in alert_list if a.key.kind() == 'Anomaly'])

    response = {
        'anomalies': anomaly_dicts
    }

    return response
