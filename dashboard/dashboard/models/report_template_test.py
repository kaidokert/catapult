# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import unittest

from google.appengine.ext import ndb

from dashboard.common import descriptor
from dashboard.common import stored_object
from dashboard.common import testing_common
from dashboard.models import report_template


@report_template.Static(
    internal_only=False,
    template_id='static-id',
    name='Test:External',
    modified=datetime.datetime.now())
def _External(unused_revisions):
  return 'external'


class ReportTest(testing_common.TestCase):

  def setUp(self):
    super(ReportTest, self).setUp()
    stored_object.Set(descriptor.PARTIAL_TEST_SUITES_KEY, [
        'TEST_PARTIAL_TEST_SUITE',
    ])
    stored_object.Set(descriptor.COMPOSITE_TEST_SUITES_KEY, [
        'TEST_PARTIAL_TEST_SUITE:COMPOSITE',
    ])
    stored_object.Set(descriptor.GROUPABLE_TEST_SUITE_PREFIXES_KEY, [
        'TEST_GROUPABLE%',
    ])
    descriptor.Descriptor.ResetMemoizedConfigurationForTesting()
    # TODO make some fake data and templates
    report_template.ReportTemplate(
        internal_only=False,
        id='ex-id',
        name='external',
        owners=[testing_common.EXTERNAL_USER.email()],
        template=dict(rows=[], statistics=[])).put()
    report_template.ReportTemplate(
        internal_only=True,
        name='internal',
        id='in-id',
        owners=[testing_common.INTERNAL_USER.email()],
        template=dict(rows=[], statistics=[])).put()

  def testInternal_PutTemplate(self):
    self.SetCurrentUser(testing_common.INTERNAL_USER.email())

    with self.assertRaises(ValueError):
      report_template.PutTemplate(
          'invalid', 'bad', [testing_common.INTERNAL_USER.email()], {})

    with self.assertRaises(ValueError):
      report_template.PutTemplate(
          'ex-id', 'bad', [testing_common.INTERNAL_USER.email()], {})
    self.assertEqual('internal', ndb.Key('ReportTemplate', 'in-id').get().name)

    with self.assertRaises(ValueError):
      report_template.PutTemplate(
          'static-id', 'bad', [testing_common.INTERNAL_USER.email()], {})

    report_template.PutTemplate(
        'in-id', 'foo', [testing_common.INTERNAL_USER.email()], {})
    self.assertEqual('foo', ndb.Key('ReportTemplate', 'in-id').get().name)

  def testAnonymous_PutTemplate(self):
    self.SetCurrentUser('')
    with self.assertRaises(ValueError):
      report_template.PutTemplate(
          'ex-id', 'foo', [testing_common.EXTERNAL_USER.email()], {})
    self.assertEqual('external', ndb.Key('ReportTemplate', 'ex-id').get().name)

  def testInternal_GetReport(self):
    self.SetCurrentUser(testing_common.INTERNAL_USER.email())
    report = report_template.GetReport('in-id', [10, 20])
    self.assertEqual('TODO', '')

  def testAnonymous_GetReport(self):
    self.SetCurrentUser('')
    self.assertEqual(None, report_template.GetReport('in-id', [10, 20]))
    report = report_template.GetReport('ex-id', [10, 20])
    self.assertEqual('TODO', '')


if __name__ == '__main__':
  unittest.main()
