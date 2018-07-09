# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import mock
import webapp2
import webtest
import unittest
import uuid

from google.appengine.api import users
from google.appengine.ext import ndb

from dashboard.api import api_auth
from dashboard.api import timeseries2
from dashboard.common import testing_common
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import graph_data
from dashboard.models import histogram
from dashboard.models import sheriff
from tracing.value.diagnostics import reserved_infos


GOOGLER_USER = users.User(email='sullivan@chromium.org',
                          _auth_domain='google.com')
NON_GOOGLE_USER = users.User(email='foo@bar.com', _auth_domain='bar.com')

_TEST_HISTOGRAM_DATA = {
    'binBoundaries': [1, [1, 1000, 20]],
    'diagnostics': {
        'buildbot': 'e9c2891d-2b04-413f-8cf4-099827e67626',
        'revisions': '25f0a111-9bb4-4cea-b0c1-af2609623160',
        'telemetry': '0bc1021b-8107-4db7-bc8c-49d7cf53c5ae'
    },
    'name': 'foo',
    'unit': 'count'
}


class Timeseries2Test(testing_common.TestCase):

  def setUp(self):
    super(Timeseries2Test, self).setUp()
    app = webapp2.WSGIApplication([
        ('/api/timeseries2', timeseries2.Timeseries2Handler)])
    self._testapp = webtest.TestApp(app)
    self._mock_oauth = None
    self._mock_internal = None
    self._MockUser(NON_GOOGLE_USER)
    sheriff.Sheriff(id='Taylor', email=GOOGLER_USER.email()).put()

  def _MockUser(self, user):
    # TODO(benjhayden): Refactor this into testing_common instead of duplicating
    # in test_suites_test.py
    if self._mock_oauth:
      self._mock_oauth.stop()
      self._mock_oauth = None
    if self._mock_internal:
      self._mock_internal.stop()
      self._mock_internal = None
    if user is None:
      return
    self._mock_oauth = mock.patch('dashboard.api.api_auth.oauth')
    self._mock_oauth.start()
    api_auth.oauth.get_current_user.return_value = user
    api_auth.oauth.get_client_id.return_value = (
        api_auth.OAUTH_CLIENT_ID_WHITELIST[0])
    self._mock_internal = mock.patch(
        'dashboard.common.utils.GetCachedIsInternalUser')
    self._mock_internal.start()
    utils.GetCachedIsInternalUser.return_value = user == GOOGLER_USER

  def _MockData(self, path='master/bot/suite/measure/case',
                internal_only=True):
    test = graph_data.TestMetadata(id=path)
    test.internal_only = internal_only
    test.improvement_direction = anomaly.DOWN
    test.units = 'units'
    test.has_rows = True
    test.put()

    for i in xrange(1, 21, 2):
      graph_data.Row(parent=test.key, id=i, value=float(i),
                     error=(i / 2.0), r_i2=(i * 2)).put()
      histogram.Histogram(
          id=str(uuid.uuid4()), test=test.key, revision=i,
          data=_TEST_HISTOGRAM_DATA, internal_only=internal_only).put()

    entity = anomaly.Anomaly()
    entity.start_revision = 10
    entity.end_revision = 11
    entity.test = test.key
    entity.is_improvement = False
    entity.internal_only = internal_only
    entity.sheriff = ndb.Key('Sheriff', 'Taylor')
    entity.median_before_anomaly = 4
    entity.median_after_anomaly = 6
    entity.put()

    histogram.SparseDiagnostic(
        id=str(uuid.uuid4()),
        test=test.key,
        start_revision=1,
        end_revision=11,
        data={'type': 'GenericSet', 'guid': str(uuid.uuid4()), 'values': [1]},
        name=reserved_infos.DEVICE_IDS.name).put()

    histogram.SparseDiagnostic(
        id=str(uuid.uuid4()),
        test=test.key,
        start_revision=11,
        end_revision=None,
        data={'type': 'GenericSet', 'guid': str(uuid.uuid4()), 'values': [2]},
        name=reserved_infos.DEVICE_IDS.name).put()

  def _Post(self, **params):
    return json.loads(self._testapp.post('/api/timeseries2', params).body)

  def testNotFound(self):
    self._MockData(internal_only=False)
    params = dict(
        test_suite='not a thing', measurement='measure', bot='master:bot',
        test_case='case', build_type='test',
        columns='revision,revisions,avg,std,alert,diagnostics,histogram')
    self._testapp.post('/api/timeseries2', params, status=404)

  def testInternalData_ExternalUser(self):
    self._MockData()
    params = dict(
        test_suite='suite', measurement='measure', bot='master:bot',
        test_case='case', build_type='test',
        columns='revision,revisions,avg,std,alert,diagnostics,histogram')
    self._testapp.post('/api/timeseries2', params, status=404)

  def testCollateAllColumns(self):
    self._MockData(internal_only=False)
    response = self._Post(
        test_suite='suite', measurement='measure', bot='master:bot',
        test_case='case', build_type='test',
        columns='revision,revisions,avg,std,alert,diagnostics,histogram')
    self.assertEqual('units', response['units'])
    self.assertEqual('down', response['improvement_direction'])
    self.assertEqual(10, len(response['data']))
    for i, datum in enumerate(response['data']):
      self.assertEqual(7, len(datum))
      self.assertEqual(1 + (2 * i), datum[0])
      self.assertEqual(2 + (4 * i), datum[1]['r_i2'])
      self.assertEqual(1 + (2 * i), datum[2])
      self.assertEqual(0.5 + i, datum[3])
      if i == 5:
        self.assertNotEqual(None, datum[4])
      else:
        self.assertEqual(None, datum[4])
      if i in [0, 5]:
        self.assertNotEqual(None, datum[5])
      else:
        self.assertEqual(None, datum[5])
      self.assertNotEqual(None, datum[6])

  def testRange(self):
    self._MockData(internal_only=False)
    response = self._Post(
        test_suite='suite', measurement='measure', bot='master:bot',
        test_case='case', build_type='test',
        min_rev=5, max_rev=15,
        columns='revision,revisions,avg,std,alert,diagnostics,histogram')
    self.assertEqual(6, len(response['data']))
    for i, datum in enumerate(response['data']):
      self.assertEqual(7, len(datum))
      self.assertEqual(5 + (2 * i), datum[0])

  def testMixOldStyleRowsWithNewStyleRows(self):
    old_count_test = graph_data.TestMetadata(
        id='master/bot/suite/measure_count/case')
    old_count_test.units = 'count'
    old_count_test.has_rows = True
    old_count_test.put()

    old_avg_test = graph_data.TestMetadata(
        id='master/bot/suite/measure_avg/case')
    old_avg_test.units = 'units'
    old_avg_test.improvement_direction = anomaly.DOWN
    old_avg_test.has_rows = True
    old_avg_test.put()

    old_std_test = graph_data.TestMetadata(
        id='master/bot/suite/measure_std/case')
    old_std_test.units = 'units'
    old_std_test.has_rows = True
    old_std_test.put()

    for i in xrange(1, 21, 2):
      graph_data.Row(parent=old_avg_test.key, id=i, value=float(i)).put()
      graph_data.Row(parent=old_std_test.key, id=i, value=(i / 2.0)).put()
      graph_data.Row(parent=old_count_test.key, id=i, value=10).put()

    new_test = graph_data.TestMetadata(id='master/bot/suite/measure/case')
    new_test.improvement_direction = anomaly.DOWN
    new_test.units = 'units'
    new_test.has_rows = True
    new_test.put()
    for i in xrange(21, 41, 2):
      graph_data.Row(parent=new_test.key, id=i, value=float(i), error=(i / 2.0),
                     d_count=10).put()

    response = self._Post(
        test_suite='suite', measurement='measure', bot='master:bot',
        test_case='case', build_type='test',
        columns='revision,avg,std,count')
    self.assertEqual('units', response['units'])
    self.assertEqual('down', response['improvement_direction'])
    self.assertEqual(20, len(response['data']))
    for i, datum in enumerate(response['data']):
      self.assertEqual(4, len(datum))
      self.assertEqual(1 + (2 * i), datum[0])
      self.assertEqual(1 + (2 * i), datum[1])
      self.assertEqual((1 + (2 * i)) / 2.0, datum[2])
      self.assertEqual(10, datum[3])


if __name__ == '__main__':
  unittest.main()
