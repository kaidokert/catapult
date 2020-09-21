# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import mock
import unittest
import uuid
import webapp2
import webtest

from dashboard import uploads_info
from dashboard.api import api_auth
from dashboard.common import testing_common
from dashboard.models import histogram
from dashboard.models import upload_completion_token
from tracing.value.diagnostics import generic_set
from tracing.value.diagnostics import reserved_infos


def SetInternalUserOAuth(mock_oauth):
  mock_oauth.get_current_user.return_value = testing_common.INTERNAL_USER
  mock_oauth.get_client_id.return_value = api_auth.OAUTH_CLIENT_ID_ALLOWLIST[0]


class UploadInfo(testing_common.TestCase):

  def setUp(self):
    super(UploadInfo, self).setUp()
    app = webapp2.WSGIApplication([
        ('/uploads/(.+)', uploads_info.UploadInfoHandler),
    ])
    self.testapp = webtest.TestApp(app)

    testing_common.SetIsInternalUser('foo@bar.com', True)
    self.SetCurrentUser('foo@bar.com')

    oauth_patcher = mock.patch.object(api_auth, 'oauth')
    self.addCleanup(oauth_patcher.stop)
    SetInternalUserOAuth(oauth_patcher.start())

  def GetFullInfoRequest(self, token_id, status=200):
    return json.loads(
        self.testapp.get(
            '/uploads/%s?additional_info=measurements' % token_id,
            status=status).body)

  def GetLimitedInfoRequest(self, token_id, status=200):
    return json.loads(
        self.testapp.get('/uploads/%s' % token_id, status=status).body)

  def testGet_Success(self):
    token_id = str(uuid.uuid4())
    token = upload_completion_token.Token(
        id=token_id, temporary_staging_file_path='file/path').put().get()

    expected = {
        'token': token_id,
        'file': 'file/path',
        'created': str(token.creation_time),
        'lastUpdated': str(token.update_time),
        'state': 'PENDING'
    }
    response = self.GetFullInfoRequest(token_id)
    self.assertEqual(response, expected)

    token.UpdateStateAsync(upload_completion_token.State.COMPLETED).wait()
    expected['state'] = 'COMPLETED'
    expected['lastUpdated'] = str(token.update_time)
    response = self.GetFullInfoRequest(token_id)
    self.assertEqual(response, expected)

  def testGet_SuccessWithMeasurements(self):
    token_id = str(uuid.uuid4())
    test_path1 = 'Chromium/win7/suite/metric1'
    test_path2 = 'Chromium/win7/suite/metric2'
    token = upload_completion_token.Token(id=token_id).put().get()
    measurement1, measurement2 = token.PopulateMeasurements({
        test_path1: False,
        test_path2: True
    })

    measurement1.state = upload_completion_token.State.COMPLETED
    measurement1.put()

    expected = {
        'token': token_id,
        'file': None,
        'created': str(token.creation_time),
        'lastUpdated': str(token.update_time),
        'state': 'PROCESSING',
        'measurements': [
            {
                'name': test_path1,
                'state': 'COMPLETED',
                'monitored': False,
                'lastUpdated': str(measurement1.update_time),
            },
            {
                'name': test_path2,
                'state': 'PROCESSING',
                'monitored': True,
                'lastUpdated': str(measurement2.update_time),
            },
        ]
    }
    response = self.GetFullInfoRequest(token_id)
    expected['measurements'].sort()
    response['measurements'].sort()
    self.assertEqual(response, expected)

  def testGet_SuccessWithMeasurementsAndAssociatedHistogram(self):
    owners_diagnostic = generic_set.GenericSet(['owner_name'])
    commit_position_diagnostic = generic_set.GenericSet([123])
    irrelevant_diagnostic = generic_set.GenericSet([42])
    owners_diagnostic.guid = str(uuid.uuid4())
    commit_position_diagnostic.guid = str(uuid.uuid4())

    histogram.SparseDiagnostic(
        id=owners_diagnostic.guid,
        data=owners_diagnostic.AsDict(),
        name=reserved_infos.OWNERS.name,
        test=None,
        start_revision=1,
        end_revision=999).put().get()

    hs = histogram.Histogram(
        id=str(uuid.uuid4()),
        data={
            'allBins': {
                '1': [1],
                '3': [1],
                '4': [1]
            },
            'binBoundaries': [1, [1, 1000, 20]],
            'diagnostics': {
                reserved_infos.CHROMIUM_COMMIT_POSITIONS.name:
                    commit_position_diagnostic.AsDict(),
                reserved_infos.OWNERS.name: owners_diagnostic.guid,
                'irrelevant_diagnostic': irrelevant_diagnostic.AsDict(),
            },
            'name': 'foo',
            'running': [3, 3, 0.5972531564093516, 2, 1, 6, 2],
            'sampleValues': [1, 2, 3],
            'unit': 'count_biggerIsBetter'
        },
        test=None,
        revision=123,
        internal_only=True).put().get()

    token_id = str(uuid.uuid4())
    test_path = 'Chromium/win7/suite/metric1'
    token = upload_completion_token.Token(id=token_id).put().get()
    measurement, = token.PopulateMeasurements({test_path: True})
    measurement.histogram = hs.key
    measurement.put()

    expected = {
        'token': token_id,
        'file': None,
        'created': str(token.creation_time),
        'lastUpdated': str(token.update_time),
        'state': 'PROCESSING',
        'measurements': [{
            'name': test_path,
            'state': 'PROCESSING',
            'monitored': True,
            'lastUpdated': str(measurement.update_time),
            'dimensions': [
                {
                    'name': reserved_infos.OWNERS.name,
                    'value': list(owners_diagnostic),
                },
                {
                    'name': reserved_infos.CHROMIUM_COMMIT_POSITIONS.name,
                    'value': list(commit_position_diagnostic),
                },
            ]
        },]
    }
    response = self.GetFullInfoRequest(token_id)
    expected['measurements'][0]['dimensions'].sort()
    response['measurements'][0]['dimensions'].sort()
    self.assertEqual(response, expected)

  def testGet_SuccessLimitedInfo(self):
    token_id = str(uuid.uuid4())
    token = upload_completion_token.Token(id=token_id).put().get()
    token.PopulateMeasurements({
        'Chromium/win7/suite/metric1': False,
        'Chromium/win7/suite/metric2': True
    })
    expected = {
        'token': token_id,
        'file': None,
        'created': str(token.creation_time),
        'lastUpdated': str(token.update_time),
        'state': 'PROCESSING',
    }
    response = self.GetLimitedInfoRequest(token_id)
    self.assertEqual(response, expected)

  @mock.patch('logging.error')
  def testGet_InvalidId(self, mock_log):
    self.GetFullInfoRequest('invalid-123&*vsd-ds', status=400)
    mock_log.assert_any_call(
        'Upload completion token id is not valid. Token id: %s',
        'invalid-123&*vsd-ds')

  @mock.patch('logging.error')
  def testGet_NotFound(self, mock_log):
    nonexistent_id = str(uuid.uuid4())
    self.GetFullInfoRequest(nonexistent_id, status=404)
    mock_log.assert_any_call('Upload completion token not found. Token id: %s',
                             nonexistent_id)

  def testGet_InvalidUser(self):
    token_id = str(uuid.uuid4())
    upload_completion_token.Token(id=token_id).put().get()

    self.SetCurrentUser('stranger@gmail.com')
    self.GetFullInfoRequest(token_id, status=403)


if __name__ == '__main__':
  unittest.main()
