# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import unittest

from google.appengine.ext import ndb

from dashboard.common import descriptor
from dashboard.common import stored_object
from dashboard.common import testing_common
from dashboard.models import anomaly
from dashboard.models import graph_data
from dashboard.models import report_template


@report_template.Static(
    internal_only=False,
    template_id='static-id',
    name='Test:External',
    modified=datetime.datetime.now())
def _External(unused_revisions):
  return 'external'


class ReportQueryTest(testing_common.TestCase):

  def setUp(self):
    super(ReportQueryTest, self).setUp()
    stored_object.Set(descriptor.PARTIAL_TEST_SUITES_KEY, [])
    stored_object.Set(descriptor.COMPOSITE_TEST_SUITES_KEY, [])
    stored_object.Set(descriptor.GROUPABLE_TEST_SUITE_PREFIXES_KEY, [])
    descriptor.Descriptor.ResetMemoizedConfigurationForTesting()

    test_path = 'master/bot/suite/measure'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    for i in [10, 20]:
      graph_data.Row(
          error=(i / 2.0),
          id=i,
          parent=test.key,
          r_i2=(i * 2),
          timestamp=datetime.datetime.utcfromtimestamp(i),
          value=float(i)).put()

    report_template.ReportTemplate(
        internal_only=False,
        id='ex-id',
        name='external',
        owners=[testing_common.EXTERNAL_USER.email()],
        template={
            'rows': [
                {
                    'testSuites': ['suite'],
                    'bots': ['master:bot'],
                    'measurement': 'measure',
                    'testCases': [],
                },
            ],
            'statistics': ['avg', 'std', 'count'],
        }).put()

  # TODO test multiple rows
  # TODO test multiple testSuites merge statistics
  # TODO test multiple bots merge statistics
  # TODO test multiple testCases merge statistics
  # TODO test empty testCases
  # TODO test ignore data from test cases that were disabled
  # TODO test ignore data from test cases that are not present for every rev in
  # the row
  # TODO test unsuffixed data rows without d_ statistics
  # TODO test unsuffixed data rows with d_ statistics
  # TODO test suffixed data rows
  # TODO test too many unsuffixed tests
  # TODO test unsuffixed test without data row falls back to suffixed tests
  # TODO test suffixed data rows missing '_avg' ignored
  # TODO test too many suffixed tests
  # TODO test too many data Row entities
  # TODO test latest revision



class ReportTemplateTest(testing_common.TestCase):

  def setUp(self):
    super(ReportTemplateTest, self).setUp()
    stored_object.Set(descriptor.PARTIAL_TEST_SUITES_KEY, [])
    stored_object.Set(descriptor.COMPOSITE_TEST_SUITES_KEY, [])
    stored_object.Set(descriptor.GROUPABLE_TEST_SUITE_PREFIXES_KEY, [])
    descriptor.Descriptor.ResetMemoizedConfigurationForTesting()

    report_template.ReportTemplate(
        internal_only=False,
        id='ex-id',
        name='external',
        owners=[testing_common.EXTERNAL_USER.email()],
        template={'rows': [], 'statistics': ['avg']}).put()
    report_template.ReportTemplate(
        internal_only=True,
        name='internal',
        id='in-id',
        owners=[testing_common.INTERNAL_USER.email()],
        template={'rows': [], 'statistics': ['avg']}).put()

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
    self.assertTrue(report['internal'])
    self.assertEqual(0, len(report['report']['rows']))
    self.assertEqual('internal', report['name'])

  def testAnonymous_GetReport(self):
    self.SetCurrentUser('')
    self.assertEqual(None, report_template.GetReport('in-id', [10, 20]))
    report = report_template.GetReport('ex-id', [10, 20])
    self.assertFalse(report['internal'])
    self.assertEqual(0, len(report['report']['rows']))
    self.assertEqual('external', report['name'])


if __name__ == '__main__':
  unittest.main()
