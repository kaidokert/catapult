# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import json
import unittest

from dashboard.api import api_auth
from dashboard.api import report
from dashboard.common import testing_common
from dashboard.models import report_template


@report_template.Static(
    internal_only=False,
    template_id='test-external',
    name='Test:External',
    modified=datetime.datetime.now())
def _External(unused_revisions):
  return 'external'


@report_template.Static(
    internal_only=True,
    template_id='test-internal',
    name='Test:Internal',
    modified=datetime.datetime.now())
def _Internal(unused_revisions):
  return 'internal'


class ReportTest(testing_common.TestCase):

  def setUp(self):
    super(ReportTest, self).setUp()
    self.SetUpApp([('/api/report', report.ReportHandler)])
    self.SetCurrentClientIdOAuth(api_auth.OAUTH_CLIENT_ID_WHITELIST[0])

  def _Post(self, **params):
    return json.loads(self.Post('/api/report', params).body)

  def testInvalid(self):
    self.Post('/api/report', dict(), status=400)
    self.Post('/api/report', dict(revisions='a'), status=400)
    self.Post('/api/report', dict(revisions='0'), status=400)
    self.Post('/api/report', dict(revisions='0', id='ghost'), status=404)

  def testInternal_PutTemplate(self):
    self.SetCurrentUserOAuth(testing_common.INTERNAL_USER)
    self.assertEqual('TODO', '')

  def testAnonymous_PutTemplate(self):
    self.SetCurrentUserOAuth(None)
    self.assertEqual('TODO', '')

  def testInternal_GetReport(self):
    self.SetCurrentUserOAuth(testing_common.INTERNAL_USER)
    self.assertEqual('TODO', '')

  def testAnonymous_GetReport(self):
    self.SetCurrentUserOAuth(None)
    self.Post('/api/report', dict(
        revisions='latest', id='test-internal'), status=404)
    result = self._Post(revisions='latest', id='test-external')
    self.assertEqual('external', result['result'])
    self.assertEqual('test-external', result['id'])
    self.assertEqual('Test:External', result['name'])
    self.assertEqual(False, result['internal'])


if __name__ == '__main__':
  unittest.main()
