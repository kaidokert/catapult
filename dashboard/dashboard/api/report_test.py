# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import unittest

from dashboard.api import api_auth
from dashboard.api import report
from dashboard.common import testing_common
from dashboard.models import report_template


class ReportTest(testing_common.TestCase):

  def setUp(self):
    super(ReportTest, self).setUp()
    self.SetUpApp([('/api/report', report.ReportHandler)])
    self.SetCurrentClientIdOAuth(api_auth.OAUTH_CLIENT_ID_WHITELIST[0])
    report_template.ReportTemplate(internal_only=False, name='external').put()
    report_template.ReportTemplate(internal_only=True, name='internal').put()

  def _Post(self, **params):
    return json.loads(self.Post('/api/report', params).body)

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
    self.assertEqual('TODO', '')


if __name__ == '__main__':
  unittest.main()
