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
    self.Post('/api/report', dict(template='template'), status=400)
    self.Post('/api/report', dict(name='name', template='template'), status=400)
    self.Post('/api/report', dict(owners='o', template='t'), status=400)

  def testInternal_PutTemplate(self):
    self.SetCurrentUserOAuth(testing_common.INTERNAL_USER)
    response = self._Post(
        owners=testing_common.INTERNAL_USER.email(),
        name='Test:New',
        template='t')
    self.assertEqual(3, len(response))
    self.assertEqual('Test:External', response[0]['name'])
    self.assertEqual('Test:Internal', response[1]['name'])
    self.assertEqual('Test:New', response[2]['name'])
    template = report_template.ReportTemplate.query(
        report_template.ReportTemplate.name == 'Test:New').get()
    self.assertEqual('t', template.template)

  def testAnonymous_PutTemplate(self):
    self.SetCurrentUserOAuth(None)
    self.Post('/api/report', dict(
        template='t', name='n', owners='o'), status=400)

  def testInternal_GetReport(self):
    self.SetCurrentUserOAuth(testing_common.INTERNAL_USER)
    response = self._Post(revisions='latest', id='test-internal')
    self.assertEqual('internal', response['report'])
    self.assertEqual('test-internal', response['id'])
    self.assertEqual('Test:Internal', response['name'])
    self.assertEqual(True, response['internal'])

  def testAnonymous_GetReport(self):
    self.SetCurrentUserOAuth(None)
    self.Post('/api/report', dict(
        revisions='latest', id='test-internal'), status=404)
    response = self._Post(revisions='latest', id='test-external')
    self.assertEqual('external', response['report'])
    self.assertEqual('test-external', response['id'])
    self.assertEqual('Test:External', response['name'])
    self.assertEqual(False, response['internal'])


if __name__ == '__main__':
  unittest.main()
