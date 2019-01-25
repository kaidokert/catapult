# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import mock

# Importing mock_oauth2_decorator before file_bug mocks out
# OAuth2Decorator usage in that file.
# pylint: disable=unused-import
from dashboard import mock_oauth2_decorator
# pylint: enable=unused-import

from dashboard import file_bug
from dashboard import file_bug_test
from dashboard.api import api_auth
from dashboard.api import new_bug
from dashboard.common import testing_common
from dashboard.models import anomaly
from dashboard.models import graph_data


class NewBugTest(testing_common.TestCase):

  def setUp(self):
    super(NewBugTest, self).setUp()
    self.SetUpApp([('/api/new_bug', new_bug.NewBugHandler)])
    self.SetCurrentClientIdOAuth(api_auth.OAUTH_CLIENT_ID_WHITELIST[0])
    self.SetCurrentUserOAuth(None)
    testing_common.SetSheriffDomains(['example.com'])

  def _Post(self, **params):
    return json.loads(self.Post('/api/new_bug', params).body)

  def testInvalidUser(self):
    self.Post('/api/new_bug', status=403)

  def testSuccess(self):
    self.PatchObject(new_bug.utils, 'ServiceAccountHttp',
                     mock.Mock(return_value=None))

    mits = mock.MagicMock()
    mits.IssueTrackerService = file_bug_test.MockIssueTrackerService
    self.PatchObject(file_bug, 'issue_tracker_service', mits)

    self.PatchObject(file_bug.app_identity, 'get_default_version_hostname',
                     mock.Mock(return_value=''))

    self.SetCurrentUserOAuth(testing_common.INTERNAL_USER)

    path = 'm/b/s/m/c'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=path,
        improvement_direction=anomaly.DOWN,
        units='units')
    test.put()
    key = anomaly.Anomaly(
        test=test.key,
        start_revision=1,
        end_revision=1).put().urlsafe()
    graph_data.Row(
        id=1,
        parent=test.key,
        value=1).put()

    response = self._Post(key=key)
    self.assertEqual(12345, response['bug_id'])
