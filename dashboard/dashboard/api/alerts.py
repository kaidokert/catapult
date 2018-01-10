# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import httplib2
import logging

from google.appengine.ext import ndb

from dashboard.api import api_request_handler
from dashboard.common import request_handler
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard import alerts
from dashboard import group_report
from dashboard import file_bug


class AlertsHandler(api_request_handler.ApiRequestHandler):
  """API handler for various alert requests."""

  def _FileBug(self):
    if not utils.IsValidSheriffUser():
      return {'error': 'Only chromium.org accounts may file bugs'}
    logging.info(self.request.headers.get('Authorization'))
    owner = self.request.get('owner')
    logging.info(owner)
    cc = self.request.get('cc')
    logging.info(cc)
    if owner and not owner.endswith('@chromium.org'):
      return {'error': 'Owner email address must end with @chromium.org'}
    summary = self.request.get('summary')
    logging.info(summary)
    description = self.request.get('description')
    logging.info(description)
    labels = self.request.get_all('label')
    logging.info(labels)
    components = self.request.get_all('component')
    logging.info(components)
    keys = self.request.get_all('key')
    logging.info(keys)
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
    # TODO(benjhayden): Remove the next line in order to file the bug using
    # the user's account. That will require changing the google-signin's
    # client-id in chromeperf-app.html to a client-id that is whitelisted by
    # the issue tracker service, which will require either adding
    # v2spa-dot-chromeperf.appspot.com to the list of domains for an
    # existing client id, or else launching v2spa to chromeperf.appspot.com.
    http = utils.ServiceAccountHttp()
    return file_bug.FileBug(
        http, keys, summary, description, labels, components, owner, cc)

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
      elif list_type.startswith('new_bug'):
        return self._FileBug()
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
