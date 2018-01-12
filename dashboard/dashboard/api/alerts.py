# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import httplib2

from google.appengine.ext import ndb

from dashboard import alerts
from dashboard import file_bug
from dashboard import group_report
from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.common import request_handler
from dashboard.common import utils
from dashboard.models import alert_group
from dashboard.models import anomaly
from dashboard.services import issue_tracker_service


class AlertsHandler(api_request_handler.ApiRequestHandler):
  """API handler for various alert requests."""

  def _AuthorizedHttp(self):
    # TODO(benjhayden): Use this instead of ServiceAccountHttp in order to use
    # the user's account. That will require changing the google-signin's
    # client-id in chromeperf-app.html to a client-id that is whitelisted by the
    # issue tracker service, which will require either adding
    # v2spa-dot-chromeperf.appspot.com to the list of domains for an existing
    # client id, or else launching v2spa to chromeperf.appspot.com.
    http = httplib2.Http()
    orig_request = http.request
    def NewRequest(uri, method='GET', body=None, headers=None,
                   redirections=httplib2.DEFAULT_MAX_REDIRECTS,
                   connection_type=None):
      headers = dict(headers or {})
      headers['Authorization'] = self.request.headers.get('Authorization')
      return orig_request(uri, method, body, headers, redirections,
                          connection_type)
    http.request = NewRequest
    return http

  def _FileBug(self):
    if not api_auth.GetCurrentUser().email().endswith('@chromium.org'):
      # TODO(benjhayden): Use IsValidSheriffUser() instead.
      raise api_request_handler.BadRequestError(
          'Only chromium.org accounts may file bugs')
    owner = self.request.get('owner')
    cc = self.request.get('cc')
    if owner and not owner.endswith('@chromium.org'):
      raise api_request_handler.BadRequestError(
          'Owner email address must end with @chromium.org')
    summary = self.request.get('summary')
    description = self.request.get('description')
    labels = self.request.get_all('label')
    components = self.request.get_all('component')
    keys = self.request.get_all('key')
    http = utils.ServiceAccountHttp()  # TODO use self._AuthorizedHttp()
    return file_bug.FileBug(
        http, keys, summary, description, labels, components, owner, cc)

  def _RecentBugs(self):
    if not api_auth.GetCurrentUser().email().endswith('@chromium.org'):
      # TODO(benjhayden): Use IsValidSheriffUser() instead.
      raise api_request_handler.BadRequestError(
          'Only chromium.org accounts may query recent bugs')
    http = utils.ServiceAccountHttp()  # TODO use self._AuthorizedHttp()
    issue_tracker = issue_tracker_service.IssueTrackerService(http)
    response = issue_tracker.List(
        q='opened-after:today-5', label='Type-Bug-Regression,Performance',
        sort='-id')
    return {'bugs': response.get('items', [])}

  def _ExistingBug(self):
    keys = self.request.get_all('key')
    bug_id = int(self.request.get('bug_id'))
    alert_entities = ndb.get_multi([ndb.Key(urlsafe=k) for k in keys])
    alert_group.ModifyAlertsAndAssociatedGroups(alert_entities, bug_id=bug_id)
    return {}

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
      elif list_type == 'new_bug':
        return self._FileBug()
      elif list_type == 'recent_bugs':
        return self._RecentBugs()
      elif list_type == 'existing_bug':
        return self._ExistingBug()
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
