# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import unittest

from google.appengine.ext import ndb

from dashboard import update_test_suite_descriptors
from dashboard.api import api_auth
from dashboard.api import report_template as api_report_template
from dashboard.common import datastore_hooks
from dashboard.common import namespaced_stored_object
from dashboard.common import stored_object
from dashboard.common import testing_common
from dashboard.models import report_template


class ReportTemplateTest(testing_common.TestCase):

  def setUp(self):
    super(ReportTemplateTest, self).setUp()
    self.SetUpApp([
        ('/api/report/template', api_report_template.ReportTemplateHandler),
    ])
    self.SetCurrentClientIdOAuth(api_auth.OAUTH_CLIENT_ID_WHITELIST[0])

    # Fake data for system_health_reports
    key = namespaced_stored_object.NamespaceKey(
        update_test_suite_descriptors.CacheKey('system_health.memory_mobile'),
        datastore_hooks.EXTERNAL)
    stored_object.Set(key, {
        'caseTags': {'health_check': []},
    })
    key = namespaced_stored_object.NamespaceKey(
        update_test_suite_descriptors.CacheKey('system_health.memory_mobile'),
        datastore_hooks.INTERNAL)
    stored_object.Set(key, {
        'caseTags': {'health_check': []},
    })

  def _Post(self, **params):
    return json.loads(self.Post('/api/report/template', params).body)

  def testUnprivileged(self):
    self.Post('/api/report/template', dict(
        owners=testing_common.INTERNAL_USER.email(),
        name='Test:New',
        template=json.dumps({'rows': []})), status=403)

  def testInvalid(self):
    self.SetCurrentUserOAuth(testing_common.INTERNAL_USER)
    self.Post('/api/report/template', dict(
        template=json.dumps({'rows': []})), status=400)
    self.Post('/api/report/template', dict(
        name='name', template=json.dumps({'rows': []})), status=400)
    self.Post('/api/report/template', dict(
        owners='o', template=json.dumps({'rows': []})), status=400)

  def testInternal_PutTemplate(self):
    self.SetCurrentUserOAuth(testing_common.INTERNAL_USER)
    response = self._Post(
        owners=testing_common.INTERNAL_USER.email(),
        name='Test:New',
        template=json.dumps({'rows': []}))
    names = [d['name'] for d in response]
    self.assertIn('Test:New', names)

    template = report_template.ReportTemplate.query(
        report_template.ReportTemplate.name == 'Test:New').get()
    self.assertEqual({'rows': []}, template.template)

  def testInternal_UpdateTemplate(self):
    self.SetCurrentUserOAuth(testing_common.INTERNAL_USER)
    response = self._Post(
        owners=testing_common.INTERNAL_USER.email(),
        name='Test:New',
        template=json.dumps({'rows': []}))
    new_id = [info['id'] for info in response if info['name'] == 'Test:New'][0]
    response = self._Post(
        owners=testing_common.INTERNAL_USER.email(),
        name='Test:Updated',
        id=new_id,
        template=json.dumps({'rows': []}))
    template = ndb.Key('ReportTemplate', new_id).get()
    self.assertEqual('Test:Updated', template.name)

  def testAnonymous_PutTemplate(self):
    self.SetCurrentUserOAuth(None)
    self.Post('/api/report/template', dict(
        template=json.dumps({'rows': []}), name='n', owners='o'), status=401)


if __name__ == '__main__':
  unittest.main()
