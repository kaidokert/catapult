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
from tracing.value import histogram as histogram_module


RunningStatistics = histogram_module.RunningStatistics


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

  def testEmptyTestCases(self):
    test_path = 'master/bot/suite/measure'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=10,
        id=10,
        parent=test.key,
        value=100).put()

    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std'],
    }
    report = report_template.ReportQuery(template, [10]).FetchSync()
    self.assertIsNone(report['rows'][0]['data'][10]['descriptors'][0]['case'])

    stats = RunningStatistics.FromDict(
        report['rows'][0]['data'][10]['statistics'])
    self.assertEqual(100, stats.mean)
    self.assertEqual(10, stats.stddev)

  def testMultipleRevisions(self):
    test_path = 'master/bot/suite/measure'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=2,
        id=10,
        parent=test.key,
        value=20).put()

    graph_data.Row(
        error=3,
        id=20,
        parent=test.key,
        value=30).put()

    graph_data.Row(
        error=4,
        id=30,
        parent=test.key,
        value=40).put()

    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std'],
    }
    report = report_template.ReportQuery(template, [10, 20, 30]).FetchSync()

    stats = RunningStatistics.FromDict(
        report['rows'][0]['data'][10]['statistics'])
    self.assertEqual(20, stats.mean)
    self.assertEqual(2, stats.stddev)

    stats = RunningStatistics.FromDict(
        report['rows'][0]['data'][20]['statistics'])
    self.assertEqual(30, stats.mean)
    self.assertEqual(3, stats.stddev)

    stats = RunningStatistics.FromDict(
        report['rows'][0]['data'][30]['statistics'])
    self.assertEqual(40, stats.mean)
    self.assertEqual(4, stats.stddev)

  def testLatestRevision(self):
    test_path = 'master/bot/suite/measure'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=2,
        id=10,
        parent=test.key,
        value=20).put()

    graph_data.Row(
        error=4,
        id=20,
        parent=test.key,
        value=40).put()

    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg'],
    }
    report = report_template.ReportQuery(template, ['latest']).FetchSync()
    import json;file('occam','a').write(json.dumps(report)+'\n')

    stats = RunningStatistics.FromDict(
        report['rows'][0]['data']['latest']['statistics'])
    self.assertEqual(40, stats.mean)
    self.assertEqual(4, stats.stddev)

  def testMultipleRows(self):
    test_path = 'master/bot/suite/a'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        id=10,
        parent=test.key,
        value=10).put()

    test_path = 'master/bot/suite/b'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        id=10,
        parent=test.key,
        value=20).put()

    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'a',
                'testCases': [],
            },
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'b',
                'testCases': [],
            },
        ],
        'statistics': ['avg'],
    }
    report = report_template.ReportQuery(template, [10]).FetchSync()

    stats = RunningStatistics.FromDict(
        report['rows'][0]['data'][10]['statistics'])
    self.assertEqual(10, stats.mean)

    stats = RunningStatistics.FromDict(
        report['rows'][1]['data'][10]['statistics'])
    self.assertEqual(20, stats.mean)

  def testMultipleTestSuites(self):
    test_path = 'master/bot/a/measure'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=1,
        id=10,
        parent=test.key,
        value=10).put()

    test_path = 'master/bot/b/measure'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=2,
        id=10,
        parent=test.key,
        value=20).put()

    template = {
        'rows': [
            {
                'testSuites': ['a', 'b'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg'],
    }
    report = report_template.ReportQuery(template, [10]).FetchSync()

    stats = RunningStatistics.FromDict(
        report['rows'][0]['data'][10]['statistics'])
    self.assertEqual(15, stats.mean)

  def testMultipleBots(self):
    test_path = 'master/a/suite/measure'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=1,
        id=10,
        parent=test.key,
        value=10).put()

    test_path = 'master/b/suite/measure'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=2,
        id=10,
        parent=test.key,
        value=20).put()

    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:a', 'master:b'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()

    stats = RunningStatistics.FromDict(
        report['rows'][0]['data'][10]['statistics'])
    self.assertEqual(15, stats.mean)

  def testMultipleTestCases(self):
    test_path = 'master/bot/suite/measure/a'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=1,
        id=10,
        parent=test.key,
        value=10).put()

    test_path = 'master/bot/suite/measure/b'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=2,
        id=10,
        parent=test.key,
        value=20).put()

    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': ['a', 'b'],
            },
        ],
        'statistics': ['avg'],
    }
    report = report_template.ReportQuery(template, [10]).FetchSync()

    stats = RunningStatistics.FromDict(
        report['rows'][0]['data'][10]['statistics'])
    self.assertEqual(15, stats.mean)

  def testIgnoreNewTestCases(self):
    test_path = 'master/bot/suite/measure/a'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=1,
        id=10,
        parent=test.key,
        value=10).put()

    graph_data.Row(
        error=1,
        id=20,
        parent=test.key,
        value=10).put()

    test_path = 'master/bot/suite/measure/b'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=2,
        id=20,
        parent=test.key,
        value=20).put()

    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': ['a', 'b'],
            },
        ],
        'statistics': ['avg'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()

    data = report['rows'][0]['data']
    self.assertEqual(1, len(data[10]['descriptors']))
    self.assertEqual('a', data[10]['descriptors'][0]['case'])
    self.assertEqual(1, len(data[20]['descriptors']))
    self.assertEqual('a', data[20]['descriptors'][0]['case'])

    stats = RunningStatistics.FromDict(data[10]['statistics'])
    self.assertEqual(10, stats.mean)

  def testCloseRevisions(self):
    test_path = 'master/bot/suite/measure/a'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=1,
        id=9,
        parent=test.key,
        value=10).put()

    graph_data.Row(
        error=1,
        id=19,
        parent=test.key,
        value=10).put()

    test_path = 'master/bot/suite/measure/b'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=2,
        id=9,
        parent=test.key,
        value=20).put()

    graph_data.Row(
        error=2,
        id=19,
        parent=test.key,
        value=20).put()

    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': ['a', 'b'],
            },
        ],
        'statistics': ['avg'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()

    data = report['rows'][0]['data']
    self.assertEqual(2, len(data[10]['descriptors']))
    self.assertEqual(2, len(data[20]['descriptors']))

    stats = RunningStatistics.FromDict(data[10]['statistics'])
    self.assertEqual(15, stats.mean)

    stats = RunningStatistics.FromDict(data[20]['statistics'])
    self.assertEqual(15, stats.mean)

  def testIgnoreRemovedTestCases(self):
    test_path = 'master/bot/suite/measure/a'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=1,
        id=10,
        parent=test.key,
        value=10).put()

    graph_data.Row(
        error=1,
        id=20,
        parent=test.key,
        value=10).put()

    test_path = 'master/bot/suite/measure/b'
    test = graph_data.TestMetadata(
        has_rows=True,
        id=test_path,
        improvement_direction=anomaly.DOWN,
        internal_only=False,
        units='units')
    test.put()

    graph_data.Row(
        error=2,
        id=10,
        parent=test.key,
        value=20).put()

    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': ['a', 'b'],
            },
        ],
        'statistics': ['avg'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()

    data = report['rows'][0]['data']
    self.assertEqual(1, len(data[10]['descriptors']))
    self.assertEqual('a', data[10]['descriptors'][0]['case'])
    self.assertEqual(1, len(data[20]['descriptors']))
    self.assertEqual('a', data[20]['descriptors'][0]['case'])

    stats = RunningStatistics.FromDict(data[10]['statistics'])
    self.assertEqual(10, stats.mean)

  def testOldStyleUnsuffixedDataRows(self):
    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std', 'count'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()
    import json;file('occam','a').write(json.dumps(report)+'\n')
    self.assertEqual('TODO', '')

  def testNewStyleUnsuffixedDataRows(self):
    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std', 'count'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()
    import json;file('occam','a').write(json.dumps(report)+'\n')
    self.assertEqual('TODO', '')

  def testSuffixedDataRows(self):
    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std', 'count'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()
    import json;file('occam','a').write(json.dumps(report)+'\n')
    self.assertEqual('TODO', '')

  def testTooManyUnsuffixedTests(self):
    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std', 'count'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()
    import json;file('occam','a').write(json.dumps(report)+'\n')
    self.assertEqual('TODO', '')

  def testFallBackToSuffixedTests(self):
    # Unsuffixed tests without data rows should fall back.
    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std', 'count'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()
    import json;file('occam','a').write(json.dumps(report)+'\n')
    self.assertEqual('TODO', '')

  def testIgnoreSuffixedDataRowsMissingAvg(self):
    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std', 'count'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()
    import json;file('occam','a').write(json.dumps(report)+'\n')
    self.assertEqual('TODO', '')

  def testIgnoreWrongUnits(self):
    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std', 'count'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()
    import json;file('occam','a').write(json.dumps(report)+'\n')
    self.assertEqual('TODO', '')

  def testTooManySuffixedTests(self):
    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std', 'count'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()
    import json;file('occam','a').write(json.dumps(report)+'\n')
    self.assertEqual('TODO', '')

  def testTooManyDataRows(self):
    template = {
        'rows': [
            {
                'testSuites': ['suite'],
                'bots': ['master:bot'],
                'measurement': 'measure',
                'testCases': [],
            },
        ],
        'statistics': ['avg', 'std', 'count'],
    }
    report = report_template.ReportQuery(template, [10, 20]).FetchSync()
    import json;file('occam','a').write(json.dumps(report)+'\n')
    self.assertEqual('TODO', '')


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
