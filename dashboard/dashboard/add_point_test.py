# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import copy
import json
import math
import unittest

import mock
import webapp2
import webtest

from google.appengine.api import datastore_errors
from google.appengine.ext import ndb

from dashboard import add_point
from dashboard import add_point_queue
from dashboard import layered_cache
from dashboard import units_to_direction
from dashboard.common import stored_object
from dashboard.common import testing_common
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import anomaly_config
from dashboard.models import graph_data
from dashboard.models import sheriff

# TODO(qyearsley): Shorten this module.
# See https://github.com/catapult-project/catapult/issues/1917
# pylint: disable=too-many-lines

# A limit to the number of entities that can be fetched. This is just an
# safe-guard to prevent possibly fetching too many entities.
_FETCH_LIMIT = 100

# Sample point which contains all of the required fields.
_SAMPLE_POINT = {
    'master': 'ChromiumPerf',
    'bot': 'win7',
    'test': 'my_test_suite/my_test',
    'revision': 12345,
    'value': 22.4,
}

# Sample Dashboard JSON v1.0 point.
_SAMPLE_DASHBOARD_JSON = {
    'master': 'ChromiumPerf',
    'bot': 'win7',
    'point_id': '12345',
    'test_suite_name': 'my_test_suite',
    'supplemental': {
        'os': 'mavericks',
        'gpu_oem': 'intel'
    },
    'versions': {
        'chrome': '12.3.45.6',
        'blink': '234567'
    },
    'chart_data': {
        'benchmark_name': 'my_benchmark',
        'benchmark_description': 'foo',
        'format_version': '1.0',
        'charts': {
            'my_test': {
                'summary': {
                    'type': 'scalar',
                    'name': 'my_test',
                    'units': 'ms',
                    'value': 22.4,
                }
            }
        }
    }
}

# Sample Dashboard JSON v1.0 point with trace data.
_SAMPLE_DASHBOARD_JSON_WITH_TRACE = {
    'master': 'ChromiumPerf',
    'bot': 'win7',
    'point_id': '12345',
    'test_suite_name': 'my_test_suite',
    'supplemental': {
        'os': 'mavericks',
        'gpu_oem': 'intel'
    },
    'versions': {
        'chrome': '12.3.45.6',
        'blink': '234567'
    },
    'chart_data': {
        'benchmark_name': 'my_benchmark',
        'benchmark_description': 'foo',
        'format_version': '1.0',
        'charts': {
            'my_test': {
                'trace1': {
                    'type': 'scalar',
                    'name': 'my_test1',
                    'units': 'ms',
                    'value': 22.4,
                },
                'trace2': {
                    'type': 'scalar',
                    'name': 'my_test2',
                    'units': 'ms',
                    'value': 33.2,
                }
            },
            'trace': {
                'trace1': {
                    'name': 'trace',
                    'type': 'trace',
                    # No cloud_url, should be handled properly
                },
                'trace2': {
                    'name': 'trace',
                    'cloud_url': 'https:\\/\\/console.developer.google.com\\/m',
                    'type': 'trace',
                }
            }
        }
    }
}

# Sample Dashboard JSON v1.0 point with a story name that should be escaped.
_SAMPLE_DASHBOARD_JSON_ESCAPE_STORYNAME = {
    'master': 'ChromiumPerf',
    'bot': 'win7',
    'point_id': '12345',
    'test_suite_name': 'my_test_suite',
    'supplemental': {
        'os': 'mavericks',
        'gpu_oem': 'intel'
    },
    'versions': {
        'chrome': '12.3.45.6',
    },
    'chart_data': {
        'benchmark_name': 'my_benchmark',
        'benchmark_description': 'foo',
        'format_version': '1.0',
        'charts': {
            'my_test': {
                'http://www.cnn.com/story': {
                    'type': 'scalar',
                    'name': 'my_test1',
                    'units': 'ms',
                    'value': 22.4,
                },
                'http://www.yahoo.com/': {
                    'type': 'scalar',
                    'name': 'my_test2',
                    'units': 'ms',
                    'value': 33.2,
                }
            }
        }
    }
}

# Units to direction to use in the tests below.
_UNITS_TO_DIRECTION_DICT = {
    'ms': {'improvement_direction': 'down'},
    'fps': {'improvement_direction': 'up'},
}

# Sample IP addresses to use in the tests below.
_WHITELISTED_IP = '123.45.67.89'


class AddPointTest(testing_common.TestCase):

  def setUp(self):
    super(AddPointTest, self).setUp()
    app = webapp2.WSGIApplication([
        ('/add_point', add_point.AddPointHandler),
        ('/add_point_queue', add_point_queue.AddPointQueueHandler)])
    self.testapp = webtest.TestApp(app)
    units_to_direction.UpdateFromJson(_UNITS_TO_DIRECTION_DICT)
    # Set up the default whitelisted IP used in the tests below.
    # Note: The behavior of responses from whitelisted and unwhitelisted IPs
    # is tested in post_data_handler_test.py.
    testing_common.SetIpWhitelist([_WHITELISTED_IP])
    self.SetCurrentUser('foo@bar.com', is_admin=True)

  @mock.patch.object(add_point_queue.find_anomalies, 'ProcessTestsAsync')
  def testPost(self, mock_process_test):
    """Tests all basic functionality of a POST request."""
    sheriff.Sheriff(
        id='my_sheriff1', email='a@chromium.org', patterns=['*/*/*/dom']).put()
    data_param = json.dumps([
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'dromaeo/dom',
            'revision': 12345,
            'value': 22.4,
            'error': 1.23,
            'supplemental_columns': {
                'r_webkit': 1355,
                'a_extra': 'hello',
                'd_median': 22.2,
            },
        },
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'dromaeo/jslib',
            'revision': 12345,
            'value': 44.3,
        }
    ])
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    # Verify everything was added to the database correctly
    rows = graph_data.Row.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(2, len(rows))

    # Verify all properties of the first Row.
    self.assertEqual(
        'ChromiumPerf/win7/dromaeo/dom', utils.TestPath(rows[0].parent_test))
    self.assertEqual('Test', rows[0].parent_test.kind())
    self.assertEqual(12345, rows[0].key.id())
    self.assertEqual(12345, rows[0].revision)
    self.assertEqual(22.4, rows[0].value)
    self.assertEqual(1.23, rows[0].error)
    self.assertEqual('1355', rows[0].r_webkit)
    self.assertEqual('hello', rows[0].a_extra)
    self.assertEqual(22.2, rows[0].d_median)
    self.assertTrue(rows[0].internal_only)

    # Verify all properties of the second Row.
    self.assertEqual(12345, rows[1].key.id())
    self.assertEqual(12345, rows[1].revision)
    self.assertEqual(44.3, rows[1].value)
    self.assertTrue(rows[1].internal_only)
    self.assertEqual(
        'ChromiumPerf/win7/dromaeo/jslib', utils.TestPath(rows[1].parent_test))
    self.assertEqual('Test', rows[1].parent_test.kind())

    # There were three TestMetadata entities inserted -- the parent test,
    # and the two child test entities in the order given.
    tests = graph_data.TestMetadata.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(3, len(tests))

    # Nothing was specified for units, so they have their default
    # values. Same for other the tests below.
    self.assertEqual('ChromiumPerf/win7/dromaeo', tests[0].key.id())
    self.assertEqual('win7', tests[0].bot.id())
    self.assertIsNone(tests[0].parent_test)
    self.assertFalse(tests[0].has_rows)
    self.assertEqual('ChromiumPerf/win7/dromaeo', tests[0].test_path)
    self.assertTrue(tests[0].internal_only)
    self.assertEqual(1, len(tests[0].monitored))
    self.assertEqual(
        'ChromiumPerf/win7/dromaeo/dom', tests[0].monitored[0].string_id())
    self.assertIsNone(tests[0].units)

    self.assertEqual('ChromiumPerf/win7/dromaeo/dom', tests[1].key.id())
    self.assertEqual('ChromiumPerf/win7/dromaeo', tests[1].parent_test.id())
    self.assertEqual('my_sheriff1', tests[1].sheriff.string_id())
    self.assertIsNone(tests[1].bot)
    self.assertTrue(tests[1].has_rows)
    self.assertEqual('ChromiumPerf/win7/dromaeo/dom', tests[1].test_path)
    self.assertTrue(tests[1].internal_only)
    self.assertIsNone(tests[1].units)

    self.assertEqual('ChromiumPerf/win7/dromaeo/jslib', tests[2].key.id())
    self.assertEqual('ChromiumPerf/win7/dromaeo', tests[2].parent_test.id())
    self.assertIsNone(tests[2].sheriff)
    self.assertIsNone(tests[2].bot)
    self.assertTrue(tests[2].has_rows)
    self.assertEqual('ChromiumPerf/win7/dromaeo/jslib', tests[2].test_path)
    self.assertTrue(tests[2].internal_only)
    self.assertIsNone(tests[2].units)

    # Both sample entries have the same master' and 'bot' values, so one
    # Master and one Bot entity were created.
    bots = graph_data.Bot.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(1, len(bots))
    self.assertEqual('win7', bots[0].key.id())
    self.assertEqual('ChromiumPerf', bots[0].key.parent().id())
    self.assertTrue(bots[0].internal_only)
    masters = graph_data.Master.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(1, len(masters))
    self.assertEqual('ChromiumPerf', masters[0].key.id())
    self.assertIsNone(masters[0].key.parent())

    # Verify that an anomaly processing was called.
    mock_process_test.assert_called_once_with([tests[1].key])

  @mock.patch.object(add_point_queue.find_anomalies, 'ProcessTestsAsync')
  def testPost_TestNameEndsWithUnderscoreRef_ProcessTestIsNotCalled(
      self, mock_process_test):
    """Tests that Tests ending with "_ref" aren't analyzed for Anomalies."""
    sheriff.Sheriff(
        id='ref_sheriff', email='a@chromium.org', patterns=['*/*/*/*']).put()
    point = copy.deepcopy(_SAMPLE_POINT)
    point['test'] = '1234/abcd_ref'
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    mock_process_test.assert_called_once_with([])

  @mock.patch.object(add_point_queue.find_anomalies, 'ProcessTestsAsync')
  def testPost_TestNameEndsWithSlashRef_ProcessTestIsNotCalled(
      self, mock_process_test):
    """Tests that leaf tests named ref aren't added to the task queue."""
    sheriff.Sheriff(
        id='ref_sheriff', email='a@chromium.org', patterns=['*/*/*/*']).put()
    point = copy.deepcopy(_SAMPLE_POINT)
    point['test'] = '1234/ref'
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    mock_process_test.assert_called_once_with([])

  @mock.patch.object(add_point_queue.find_anomalies, 'ProcessTestsAsync')
  def testPost_TestNameEndsContainsButDoesntEndWithRef_ProcessTestIsCalled(
      self, mock_process_test):
    sheriff.Sheriff(
        id='ref_sheriff', email='a@chromium.org', patterns=['*/*/*/*']).put()
    point = copy.deepcopy(_SAMPLE_POINT)
    point['test'] = '_ref/abcd'
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    self.assertTrue(mock_process_test.called)

  def testPost_TestPathTooLong_PointRejected(self):
    """Tests that an error is returned when the test path would be too long."""
    point = copy.deepcopy(_SAMPLE_POINT)
    point['test'] = 'long_test/%s' % ('x' * 490)
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    tests = graph_data.TestMetadata.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(0, len(tests))

  def testPost_TrailingSlash_Ignored(self):
    point = copy.deepcopy(_SAMPLE_POINT)
    point['test'] = 'mach_ports_parent/mach_ports/'
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    tests = graph_data.TestMetadata.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(2, len(tests))
    self.assertEqual('ChromiumPerf/win7/mach_ports_parent', tests[0].key.id())
    self.assertEqual(
        'ChromiumPerf/win7/mach_ports_parent/mach_ports', tests[1].key.id())
    self.assertEqual(
        'ChromiumPerf/win7/mach_ports_parent', tests[1].parent_test.id())

  def testPost_LeadingSlash_Ignored(self):
    point = copy.deepcopy(_SAMPLE_POINT)
    point['test'] = '/boot_time/pre_plugin_time'
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    tests = graph_data.TestMetadata.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(2, len(tests))
    self.assertEqual('ChromiumPerf/win7/boot_time', tests[0].key.id())
    self.assertEqual(
        'ChromiumPerf/win7/boot_time/pre_plugin_time', tests[1].key.id())
    self.assertEqual('ChromiumPerf/win7/boot_time', tests[1].parent_test.id())

  def testPost_BadJson_DataRejected(self):
    """Tests that an error is returned when the given data is not valid JSON."""
    self.testapp.post(
        '/add_point', {'data': "This isn't JSON"}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

  def testPost_BadGraphName_DataRejected(self):
    """Tests that an error is returned when the test name has too many parts."""
    point = copy.deepcopy(_SAMPLE_POINT)
    point['test'] = 'a/b/c/d/e/f/g/h/i/j/k'
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

  def testPost_BadBenchmarkName_DataRejected(self):
    """Tests that an error is returned when the test name has too many parts."""
    point = copy.deepcopy(_SAMPLE_DASHBOARD_JSON)
    point['test_suite_name'] = 'no/slashes'
    response = self.testapp.post(
        '/add_point', {'data': json.dumps(point)}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.assertIn('Illegal slash in test suite name', response.body)

  def testPost_TestNameHasDoubleUnderscores_Rejected(self):
    point = copy.deepcopy(_SAMPLE_POINT)
    point['test'] = 'my_test_suite/__my_test__'
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

  @mock.patch('logging.error')
  @mock.patch.object(graph_data.Master, 'get_by_id')
  def testPost_BadRequestError_ErrorLogged(
      self, mock_get_by_id, mock_logging_error):
    """Tests that error is logged if a datastore BadRequestError happens."""
    mock_get_by_id.side_effect = datastore_errors.BadRequestError
    self.testapp.post(
        '/add_point', {'data': json.dumps([_SAMPLE_POINT])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    self.assertEqual(1, len(mock_logging_error.mock_calls))

  def testPost_IncompleteData_DataRejected(self):
    """Tests that an error is returned when the given columns are invalid."""
    data_param = json.dumps([
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'foo/bar/baz',
        }
    ])
    self.testapp.post(
        '/add_point', {'data': data_param}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

  def testPost_NoRevisionAndNoVersionNums_Rejected(self):
    """Asserts post fails when both revision and version numbers are missing."""
    data_param = json.dumps([
        {
            'master': 'CrosPerf',
            'bot': 'lumpy',
            'test': 'mach_ports/mach_ports/',
            'value': '231.666666667',
            'error': '2.28521820013',
        }
    ])
    self.testapp.post(
        '/add_point', {'data': data_param}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

  def testPost_InvalidRevision_Rejected(self):
    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 'I am not a valid revision number!'
    response = self.testapp.post(
        '/add_point', {'data': json.dumps([point])}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.assertIn(
        'Bad value for "revision", should be numerical.\n', response.body)

  def testPost_InvalidSupplementalRevision_DropsRevision(self):
    point = copy.deepcopy(_SAMPLE_POINT)
    point['supplemental_columns'] = {
        'r_one': '1234',
        'r_two': 'I am not a valid revision or version.',
    }
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    # Supplemental revision numbers with an invalid format should be dropped.
    row = graph_data.Row.query().get()
    self.assertEqual('1234', row.r_one)
    self.assertFalse(hasattr(row, 'r_two'))

  def testPost_UnWhitelistedBots_MarkedInternalOnly(self):
    stored_object.Set(
        add_point_queue.BOT_WHITELIST_KEY, ['linux-release', 'win7'])
    parent = graph_data.Master(id='ChromiumPerf').put()
    parent = graph_data.Bot(
        id='suddenly_secret', parent=parent, internal_only=False).put()
    graph_data.TestMetadata(
        id='ChromiumPerf/suddenly_secret/dromaeo', internal_only=False).put()

    data_param = json.dumps([
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'dromaeo/dom',
            'value': '33.2',
            'revision': '1234',
        },
        {
            'master': 'ChromiumPerf',
            'bot': 'very_secret',
            'test': 'dromaeo/dom',
            'value': '100.1',
            'revision': '1234',
        },
        {
            'master': 'ChromiumPerf',
            'bot': 'suddenly_secret',
            'test': 'dromaeo/dom',
            'value': '22.3',
            'revision': '1234',
        },
    ])
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    bots = graph_data.Bot.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(3, len(bots))
    self.assertEqual('suddenly_secret', bots[0].key.string_id())
    self.assertTrue(bots[0].internal_only)
    self.assertEqual('very_secret', bots[1].key.string_id())
    self.assertTrue(bots[1].internal_only)
    self.assertEqual('win7', bots[2].key.string_id())
    self.assertFalse(bots[2].internal_only)

    tests = graph_data.TestMetadata.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(6, len(tests))
    self.assertEqual(
        'ChromiumPerf/suddenly_secret/dromaeo', tests[0].key.string_id())
    self.assertEqual('suddenly_secret', tests[0].bot.string_id())
    self.assertTrue(tests[0].internal_only)
    self.assertEqual(
        'ChromiumPerf/suddenly_secret/dromaeo/dom', tests[1].key.string_id())
    self.assertTrue(tests[1].internal_only)
    self.assertEqual(
        'ChromiumPerf/very_secret/dromaeo', tests[2].key.string_id())
    self.assertEqual('very_secret', tests[2].bot.string_id())
    self.assertTrue(tests[2].internal_only)
    self.assertEqual(
        'ChromiumPerf/very_secret/dromaeo/dom', tests[3].key.string_id())
    self.assertTrue(tests[3].internal_only)
    self.assertEqual('ChromiumPerf/win7/dromaeo', tests[4].key.string_id())
    self.assertEqual('win7', tests[4].bot.string_id())
    self.assertFalse(tests[4].internal_only)
    self.assertEqual('ChromiumPerf/win7/dromaeo/dom', tests[5].key.string_id())
    self.assertFalse(tests[5].internal_only)

    rows = graph_data.Row.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(3, len(rows))
    self.assertTrue(rows[0].internal_only)
    self.assertTrue(rows[1].internal_only)
    self.assertFalse(rows[2].internal_only)

  @mock.patch.object(
      add_point_queue.find_anomalies, 'ProcessTestsAsync', mock.MagicMock())
  def testPost_NewTest_SheriffPropertyIsAdded(self):
    """Tests that sheriffs are added to tests when Tests are created."""
    sheriff1 = sheriff.Sheriff(
        id='sheriff1', email='a@chromium.org',
        patterns=['ChromiumPerf/*/*/jslib']).put()
    sheriff2 = sheriff.Sheriff(
        id='sheriff2', email='a@chromium.org',
        patterns=['*/*/image_benchmark/*', '*/*/scrolling_benchmark/*']).put()

    data_param = json.dumps([
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'scrolling_benchmark/mean_frame_time',
            'revision': 123456,
            'value': 700,
        },
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'dromaeo/jslib',
            'revision': 123445,
            'value': 200,
        },
        {
            'master': 'ChromiumWebkit',
            'bot': 'win7',
            'test': 'dromaeo/jslib',
            'revision': 12345,
            'value': 205.3,
        }
    ])
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    sheriff1_test = ndb.Key(
        'TestMetadata', 'ChromiumPerf/win7/dromaeo/jslib').get()
    self.assertEqual(sheriff1, sheriff1_test.sheriff)

    sheriff2_test = ndb.Key(
        'TestMetadata',
        'ChromiumPerf/win7/scrolling_benchmark/mean_frame_time').get()
    self.assertEqual(sheriff2, sheriff2_test.sheriff)

    no_sheriff_test = ndb.Key(
        'TestMetadata', 'ChromiumWebkit/win7/dromaeo/jslib').get()
    self.assertIsNone(no_sheriff_test.sheriff)

    test_suite = ndb.Key(
        'TestMetadata', 'ChromiumPerf/win7/scrolling_benchmark').get()
    self.assertEqual(1, len(test_suite.monitored))
    self.assertEqual(
        'ChromiumPerf/win7/scrolling_benchmark/mean_frame_time',
        test_suite.monitored[0].string_id())

  def testPost_NewTest_AnomalyConfigPropertyIsAdded(self):
    """Tests that AnomalyConfig keys are added to TestMetadata upon creation.

    Like with sheriffs, AnomalyConfig keys are to added to TestMetadata when the
    TestMetadata is put if the test path matches the pattern of the
    AnomalyConfig.
    """
    anomaly_config1 = anomaly_config.AnomalyConfig(
        id='anomaly_config1', config='',
        patterns=['ChromiumPerf/*/dromaeo/jslib']).put()
    anomaly_config2 = anomaly_config.AnomalyConfig(
        id='anomaly_config2', config='',
        patterns=['*/*image_benchmark/*', '*/*/scrolling_benchmark/*']).put()

    data_param = json.dumps([
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'scrolling_benchmark/mean_frame_time',
            'revision': 123456,
            'value': 700,
        },
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'dromaeo/jslib',
            'revision': 123445,
            'value': 200,
        },
        {
            'master': 'ChromiumWebkit',
            'bot': 'win7',
            'test': 'dromaeo/jslib',
            'revision': 12345,
            'value': 205.3,
        }
    ])
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    anomaly_config1_test = ndb.Key(
        'TestMetadata', 'ChromiumPerf/win7/dromaeo/jslib').get()
    self.assertEqual(
        anomaly_config1, anomaly_config1_test.overridden_anomaly_config)

    anomaly_config2_test = ndb.Key(
        'TestMetadata',
        'ChromiumPerf/win7/scrolling_benchmark/mean_frame_time').get()
    self.assertEqual(
        anomaly_config2, anomaly_config2_test.overridden_anomaly_config)

    no_config_test = ndb.Key(
        'TestMetadata', 'ChromiumWebkit/win7/dromaeo/jslib').get()
    self.assertIsNone(no_config_test.overridden_anomaly_config)

  def testPost_NewTest_ClosestsAnomlyConfigIsUsed(self):
    anomaly_config.AnomalyConfig(
        id='anomaly_config1', config='',
        patterns=['ChromiumPerf/*/dromaeo/*']).put()
    anomaly_config2 = anomaly_config.AnomalyConfig(
        id='anomaly_config2', config='',
        patterns=['ChromiumPerf/*/dromaeo/benchmark_duration']).put()
    anomaly_config.AnomalyConfig(
        id='anomaly_config3', config='',
        patterns=['ChromiumPerf/*/*/*']).put()

    data_param = json.dumps([
        {
            'master': 'ChromiumPerf',
            'bot': 'win',
            'test': 'dromaeo/benchmark_duration',
            'revision': 123456,
            'value': 700,
        }
    ])
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    anomaly_config1_test = ndb.Key(
        'TestMetadata', 'ChromiumPerf/win/dromaeo/benchmark_duration').get()
    self.assertEqual(
        anomaly_config2, anomaly_config1_test.overridden_anomaly_config)

  def testPost_NewTest_AddsUnits(self):
    """Checks units and improvement direction are added for new TestMetadata."""
    data_param = json.dumps([
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'scrolling_benchmark/mean_frame_time',
            'revision': 123456,
            'value': 700,
            'units': 'ms',
        }
    ])
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    tests = graph_data.TestMetadata.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(2, len(tests))
    self.assertEqual(
        'ChromiumPerf/win7/scrolling_benchmark', tests[0].key.string_id())
    self.assertIsNone(tests[0].units)
    self.assertEqual(anomaly.UNKNOWN, tests[0].improvement_direction)
    self.assertEqual(
        'ChromiumPerf/win7/scrolling_benchmark/mean_frame_time',
        tests[1].key.string_id())
    self.assertEqual('ms', tests[1].units)
    self.assertEqual(anomaly.DOWN, tests[1].improvement_direction)

  def testPost_NewPointWithNewUnits_TestUnitsAreUpdated(self):
    parent = graph_data.Master(id='ChromiumPerf').put()
    parent = graph_data.Bot(id='win7', parent=parent).put()
    parent = graph_data.TestMetadata(
        id='ChromiumPerf/win7/scrolling_benchmark').put()
    graph_data.TestMetadata(
        id='ChromiumPerf/win7/scrolling_benchmark/mean_frame_time',
        units='ms',
        improvement_direction=anomaly.DOWN).put()

    data_param = json.dumps([
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'scrolling_benchmark/mean_frame_time',
            'revision': 123456,
            'value': 700,
            'units': 'fps',
        }
    ])
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    tests = graph_data.TestMetadata.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(2, len(tests))
    self.assertEqual(
        'ChromiumPerf/win7/scrolling_benchmark', tests[0].key.string_id())
    self.assertIsNone(tests[0].units)
    self.assertEqual(anomaly.UNKNOWN, tests[0].improvement_direction)
    self.assertEqual(
        'ChromiumPerf/win7/scrolling_benchmark/mean_frame_time',
        tests[1].key.string_id())
    self.assertEqual('fps', tests[1].units)
    self.assertEqual(anomaly.UP, tests[1].improvement_direction)

  def testPost_NewPoint_UpdatesImprovementDirection(self):
    """Tests that adding a point updates units for an existing TestMetadata."""
    parent = graph_data.Master(id='ChromiumPerf').put()
    parent = graph_data.Bot(id='win7', parent=parent).put()
    parent = graph_data.TestMetadata(
        id='ChromiumPerf/win7/scrolling_benchmark').put()
    frame_time_key = graph_data.TestMetadata(
        id='ChromiumPerf/win7/scrolling_benchmark/frame_time', units='ms',
        improvement_direction=anomaly.DOWN).put()
    # Before sending the new data point, the improvement direction is down.
    test = frame_time_key.get()
    self.assertEqual(anomaly.DOWN, test.improvement_direction)
    data_param = json.dumps([
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'scrolling_benchmark/frame_time',
            'revision': 123456,
            'value': 700,
            'units': 'ms',
            'higher_is_better': True,
        }
    ])
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    # After sending the new data which explicitly specifies an improvement
    # direction, the improvement direction is changed even though the units
    # (ms) usually indicates an improvement direction of down.
    test = frame_time_key.get()
    self.assertEqual(anomaly.UP, test.improvement_direction)

  def testPost_DirectionUpdatesWithUnitMap(self):
    """Tests that adding a point updates units for an existing TestMetadata."""
    parent = graph_data.Master(id='ChromiumPerf').put()
    parent = graph_data.Bot(id='win7', parent=parent).put()
    parent = graph_data.TestMetadata(
        id='ChromiumPerf/win7/scrolling_benchmark').put()
    graph_data.TestMetadata(
        id='ChromiumPerf/win7/scrolling_benchmark/mean_frame_time',
        units='ms',
        improvement_direction=anomaly.UNKNOWN).put()
    point = {
        'master': 'ChromiumPerf',
        'bot': 'win7',
        'test': 'scrolling_benchmark/mean_frame_time',
        'revision': 123456,
        'value': 700,
        'units': 'ms',
    }
    self.testapp.post('/add_point',
                      {'data': json.dumps([point])},
                      extra_environ={'REMOTE_ADDR': '123.45.67.89'})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    tests = graph_data.TestMetadata.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(2, len(tests))
    self.assertEqual(
        'ChromiumPerf/win7/scrolling_benchmark', tests[0].key.string_id())
    self.assertIsNone(tests[0].units)
    self.assertEqual(anomaly.UNKNOWN, tests[0].improvement_direction)
    self.assertEqual(
        'ChromiumPerf/win7/scrolling_benchmark/mean_frame_time',
        tests[1].key.string_id())
    self.assertEqual('ms', tests[1].units)
    self.assertEqual(anomaly.DOWN, tests[1].improvement_direction)

  def testPost_AddNewPointToDeprecatedTest_ResetsDeprecated(self):
    """Tests that adding a point sets the test to be non-deprecated."""
    parent = graph_data.Master(id='ChromiumPerf').put()
    parent = graph_data.Bot(id='win7', parent=parent).put()
    graph_data.TestMetadata(
        id='ChromiumPerf/win7/scrolling_benchmark', deprecated=True).put()
    graph_data.TestMetadata(
        id='ChromiumPerf/win7/scrolling_benchmark/mean_frame_time',
        deprecated=True).put()

    point = {
        'master': 'ChromiumPerf',
        'bot': 'win7',
        'test': 'scrolling_benchmark/mean_frame_time',
        'revision': 123456,
        'value': 700,
    }
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    tests = graph_data.TestMetadata.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(2, len(tests))
    # Note that the parent test is also marked as non-deprecated.
    self.assertEqual(
        'ChromiumPerf/win7/scrolling_benchmark', tests[0].key.string_id())
    self.assertFalse(tests[0].deprecated)
    self.assertEqual(
        'ChromiumPerf/win7/scrolling_benchmark/mean_frame_time',
        tests[1].key.string_id())
    self.assertFalse(tests[1].deprecated)

  def testPost_GitHashSupplementalRevision_Accepted(self):
    """Tests that git hashes can be added as supplemental revision columns."""
    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 123
    point['supplemental_columns'] = {
        'r_chromium_rev': '2eca27b067e3e57c70e40b8b95d0030c5d7c1a7f',
        'r_webkit_rev': 'bf9aa8d62561bb2e4d7bc09e9d9e8c6a665ddc88',
    }
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    rows = graph_data.Row.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(1, len(rows))
    self.assertEqual(123, rows[0].key.id())
    self.assertEqual(123, rows[0].revision)
    self.assertEqual(
        '2eca27b067e3e57c70e40b8b95d0030c5d7c1a7f', rows[0].r_chromium_rev)
    self.assertEqual(
        'bf9aa8d62561bb2e4d7bc09e9d9e8c6a665ddc88', rows[0].r_webkit_rev)

  def testPost_NewSuite_CachedSubTestsDeleted(self):
    """Tests that cached test lists are cleared as new test suites are added."""
    # Set the cached test lists. Note that no actual TestMetadata entities are
    # added here, so when a new point is added, it will still count as a new
    # TestMetadata.
    layered_cache.Set(
        graph_data.LIST_TESTS_SUBTEST_CACHE_KEY % (
            'ChromiumPerf', 'win7', 'scrolling_benchmark'),
        {'foo': 'bar'})
    layered_cache.Set(
        graph_data.LIST_TESTS_SUBTEST_CACHE_KEY % (
            'ChromiumPerf', 'mac', 'scrolling_benchmark'),
        {'foo': 'bar'})
    data_param = json.dumps([
        {
            'master': 'ChromiumPerf',
            'bot': 'win7',
            'test': 'scrolling_benchmark/mean_frame_time',
            'revision': 123456,
            'value': 700,
        }
    ])
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    # Subtests for ChromiumPerf/win7/scrolling_benchmark should be cleared.
    self.assertIsNone(layered_cache.Get(
        graph_data.LIST_TESTS_SUBTEST_CACHE_KEY % (
            'ChromiumPerf', 'win7', 'scrolling_benchmark')))
    # Subtests for another bot should NOT be cleared.
    self.assertEqual({'foo': 'bar'}, layered_cache.Get(
        graph_data.LIST_TESTS_SUBTEST_CACHE_KEY % (
            'ChromiumPerf', 'mac', 'scrolling_benchmark')))

  def testParseColumns(self):
    """Tests that the GetAndValidateRowProperties method handles valid data."""
    expected = {
        'value': 444.55,
        'error': 12.3,
        'r_webkit': '12345',
        'r_skia': '43210',
        'a_note': 'hello',
        'd_run_1': 444.66,
        'd_run_2': 444.44,
    }
    actual = add_point.GetAndValidateRowProperties(
        {
            'revision': 12345,
            'value': 444.55,
            'error': 12.3,
            'supplemental_columns': {
                'r_webkit': 12345,
                'r_skia': 43210,
                'a_note': 'hello',
                'd_run_1': 444.66,
                'd_run_2': 444.44,
            },
        }
    )
    self.assertEqual(expected, actual)

  def testPost_NoValue_Rejected(self):
    """Tests the error returned when no "value" is given."""
    point = copy.deepcopy(_SAMPLE_POINT)
    del point['value']
    response = self.testapp.post(
        '/add_point', {'data': json.dumps([point])}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.assertIn('No "value" given.\n', response.body)
    self.assertIsNone(graph_data.Row.query().get())

  def testPost_WithBadValue_Rejected(self):
    """Tests the error returned when an invalid "value" is given."""
    point = copy.deepcopy(_SAMPLE_POINT)
    point['value'] = 'hello'
    response = self.testapp.post(
        '/add_point', {'data': json.dumps([point])}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    self.assertIn(
        'Bad value for "value", should be numerical.\n', response.body)
    self.assertIsNone(graph_data.Row.query().get())

  def testPost_WithBadPointErrorValue_ErrorValueDropped(self):
    point = copy.deepcopy(_SAMPLE_POINT)
    point['error'] = 'not a number'
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    row = graph_data.Row.query().get()
    self.assertIsNone(row.error)

  def testPost_TooManyColumns_SomeColumnsDropped(self):
    """Tests that some columns are dropped if there are too many."""
    point = copy.deepcopy(_SAMPLE_POINT)
    supplemental_columns = {}
    for i in range(1, add_point._MAX_NUM_COLUMNS * 2):
      supplemental_columns['d_run_%d' % i] = i
    point['supplemental_columns'] = supplemental_columns
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    row = graph_data.Row.query().get()
    row_dict = row.to_dict()
    data_columns = [c for c in row_dict if c.startswith('d_')]
    self.assertGreater(len(data_columns), 1)
    self.assertLessEqual(len(data_columns), add_point._MAX_NUM_COLUMNS)

  def testPost_BadSupplementalColumnName_ColumnDropped(self):
    point = copy.deepcopy(_SAMPLE_POINT)
    point['supplemental_columns'] = {'q_foo': 'bar'}

    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    # Supplemental columns with undefined prefixes should be dropped.
    row = graph_data.Row.query().get()
    self.assertFalse(hasattr(row, 'q_foo'))

  def testPost_LongSupplementalColumnName_ColumnDropped(self):
    point = copy.deepcopy(_SAMPLE_POINT)
    key = 'a_' + ('a' * add_point._MAX_COLUMN_NAME_LENGTH)
    point['supplemental_columns'] = {
        key: '1234',
    }
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    # Supplemental columns with super long names should be dropped.
    row = graph_data.Row.query().get()
    self.assertFalse(hasattr(row, key))

  def testPost_LongSupplementalAnnotation_ColumnDropped(self):
    point = copy.deepcopy(_SAMPLE_POINT)
    point['supplemental_columns'] = {
        'a_one': 'z' * (add_point._STRING_COLUMN_MAX_LENGTH + 1),
        'a_two': 'hello',
    }
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    # Row properties with names that are too long are not added.
    row = graph_data.Row.query().get()
    self.assertFalse(hasattr(row, 'a_one'))
    self.assertEqual('hello', row.a_two)

  def testPost_BadSupplementalDataColumn_ColumnDropped(self):
    """Tests that bad supplemental data columns are dropped."""
    point = copy.deepcopy(_SAMPLE_POINT)
    point['supplemental_columns'] = {
        'd_run_1': 'hello',
        'd_run_2': 42.5,
    }
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    # Row data properties that aren't numerical aren't added.
    row = graph_data.Row.query().get()
    self.assertFalse(hasattr(row, 'd_run_1'))
    self.assertEqual(42.5, row.d_run_2)

  def testPost_RevisionTooLow_Rejected(self):
    # If a point's ID is much lower than the last one, it should be rejected
    # because this indicates that the revision type was accidentally changed.
    # First add one point; it's accepted because it's the first in the series.
    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 1408479179
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    test_path = 'ChromiumPerf/win7/my_test_suite/my_test'
    last_added_revision = ndb.Key('LastAddedRevision', test_path).get()
    self.assertEqual(1408479179, last_added_revision.revision)

    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 285000
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    rows = graph_data.Row.query().fetch()
    self.assertEqual(1, len(rows))

  def testPost_RevisionTooHigh_Rejected(self):
    # First add one point; it's accepted because it's the first in the series.
    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 285000
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 1408479179
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    rows = graph_data.Row.query().fetch()
    self.assertEqual(1, len(rows))

  def testPost_RevisionTooHigh_SpecialCasedBot_Accepted(self):
    # First add one point; it's accepted because it's the first in the series.
    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 285000
    point['master'] = 'SpecialBotQA'
    point['bot'] = 'release-tests-bot'
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)

    # Second point is too high, but is also accepted because of bot and
    # master name.
    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 1471538371
    point['master'] = 'SpecialBotQA'
    point['bot'] = 'release-tests-bot'
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    rows = graph_data.Row.query().fetch()
    self.assertEqual(2, len(rows))

  def testPost_MultiplePointsWithCloseRevisions_Accepted(self):
    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 285000
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 285200
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    point = copy.deepcopy(_SAMPLE_POINT)
    point['revision'] = 285100
    self.testapp.post(
        '/add_point', {'data': json.dumps([point])},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    rows = graph_data.Row.query().fetch()
    self.assertEqual(3, len(rows))

  def testPost_ValidRow_CorrectlyAdded(self):
    """Tests that adding a chart causes the correct row to be added."""
    data_param = json.dumps(_SAMPLE_DASHBOARD_JSON)
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    rows = graph_data.Row.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(1, len(rows))
    self.assertEqual(12345, rows[0].revision)
    self.assertEqual(22.4, rows[0].value)
    self.assertEqual(0, rows[0].error)
    self.assertEqual('12.3.45.6', rows[0].r_chrome)
    self.assertEqual('234567', rows[0].r_blink)
    self.assertEqual('mavericks', rows[0].a_os)
    self.assertEqual('intel', rows[0].a_gpu_oem)
    test_suite = ndb.Key(
        'TestMetadata', 'ChromiumPerf/win7/my_test_suite').get()
    self.assertEqual('foo', test_suite.description)

  def testPost_NoTestSuiteName_BenchmarkNameUsed(self):
    sample = copy.deepcopy(_SAMPLE_DASHBOARD_JSON)
    del sample['test_suite_name']
    data_param = json.dumps(sample)
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    self.assertIsNone(utils.TestKey('ChromiumPerf/win7/my_test_suite').get())
    self.assertIsNotNone(utils.TestKey('ChromiumPerf/win7/my_benchmark').get())

  def testPost_TestSuiteNameIsNone_BenchmarkNameUsed(self):
    sample = copy.deepcopy(_SAMPLE_DASHBOARD_JSON)
    sample['test_suite_name'] = None
    data_param = json.dumps(sample)
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    self.assertIsNone(utils.TestKey('ChromiumPerf/win7/my_test_suite').get())
    self.assertIsNotNone(utils.TestKey('ChromiumPerf/win7/my_benchmark').get())

  def testPost_FormatV1_CorrectlyAdded(self):
    """Tests that adding a chart causes the correct trace to be added."""
    data_param = json.dumps(_SAMPLE_DASHBOARD_JSON_WITH_TRACE)
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    rows = graph_data.Row.query().fetch(limit=_FETCH_LIMIT)
    self.assertEqual(2, len(rows))
    self.assertEqual(12345, rows[0].revision)
    self.assertEqual(22.4, rows[0].value)
    self.assertEqual(0, rows[0].error)
    self.assertEqual('12.3.45.6', rows[0].r_chrome)
    self.assertFalse(hasattr(rows[0], 'a_tracing_uri'))
    self.assertEqual(33.2, rows[1].value)
    self.assertEqual('https://console.developer.google.com/m',
                     rows[1].a_tracing_uri)

  def testPost_FormatV1_StoryNameEscaped(self):
    data_param = json.dumps(_SAMPLE_DASHBOARD_JSON_ESCAPE_STORYNAME)
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    k = ndb.Key(
        'TestMetadata',
        'ChromiumPerf/win7/my_test_suite/my_test/http___www.cnn.com_story')
    t = k.get()
    self.assertEqual('http://www.cnn.com/story', t.unescaped_story_name)
    k = ndb.Key(
        'TestMetadata',
        'ChromiumPerf/win7/my_test_suite/my_test/http___www.yahoo.com_')
    t = k.get()
    self.assertEqual('http://www.yahoo.com/', t.unescaped_story_name)

  def testPost_FormatV1_StoryNameEscapedUpdated(self):
    t = graph_data.TestMetadata(
        id='ChromiumPerf/win7/my_test_suite/my_test/http___www.cnn.com_story',
        description='bar')
    t.put()
    self.assertEqual(None, t.unescaped_story_name)
    data_param = json.dumps(_SAMPLE_DASHBOARD_JSON_ESCAPE_STORYNAME)
    self.testapp.post(
        '/add_point', {'data': data_param},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    self.ExecuteTaskQueueTasks('/add_point_queue', add_point._TASK_QUEUE_NAME)
    k = ndb.Key(
        'TestMetadata',
        'ChromiumPerf/win7/my_test_suite/my_test/http___www.cnn.com_story')
    t = k.get()
    self.assertEqual('http://www.cnn.com/story', t.unescaped_story_name)

  def testPost_FormatV1_BadCharts_Rejected(self):
    chart = copy.deepcopy(_SAMPLE_DASHBOARD_JSON)
    chart['chart_data']['charts'] = {'test': False}
    self.testapp.post(
        '/add_point', {'data': json.dumps(chart)}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

  def testPost_FormatV1_BadMaster_Rejected(self):
    """Tests that attempting to post with no master name will error."""
    chart = copy.deepcopy(_SAMPLE_DASHBOARD_JSON)
    del chart['master']
    self.testapp.post(
        '/add_point', {'data': json.dumps(chart)}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

  def testPost_FormatV1_BadBot_Rejected(self):
    """Tests that attempting to post with no bot name will error."""
    chart = copy.deepcopy(_SAMPLE_DASHBOARD_JSON)
    del chart['bot']
    self.testapp.post(
        '/add_point', {'data': json.dumps(chart)}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

  def testPost_FormatV1_BadPointId_Rejected(self):
    """Tests that attempting to post a chart no point id will error."""
    chart = copy.deepcopy(_SAMPLE_DASHBOARD_JSON)
    del chart['point_id']
    self.testapp.post(
        '/add_point', {'data': json.dumps(chart)}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

  def testPost_GarbageDict_Rejected(self):
    """Tests that posting an ill-formatted dict will error."""
    chart = {'foo': 'garbage'}
    self.testapp.post(
        '/add_point', {'data': json.dumps(chart)}, status=400,
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})

  def testPost_FormatV1_EmptyCharts_NothingAdded(self):
    chart = copy.deepcopy(_SAMPLE_DASHBOARD_JSON)
    chart['chart_data']['charts'] = {}
    self.testapp.post(
        '/add_point', {'data': json.dumps(chart)},
        extra_environ={'REMOTE_ADDR': _WHITELISTED_IP})
    # Status is OK, but no rows are added.
    self.assertIsNone(graph_data.Row.query().get())


class FlattenTraceTest(testing_common.TestCase):

  def testDashboardJsonToRawRows_WithIsRef(self):
    """Tests that rows from a chart from a ref build have the correct name."""
    chart = copy.deepcopy(_SAMPLE_DASHBOARD_JSON)
    chart['is_ref'] = True
    rows = add_point._DashboardJsonToRawRows(chart)
    self.assertEqual('my_test_suite/my_test/ref', rows[0]['test'])

  @staticmethod
  def _SampleTrace():
    return {
        'name': 'bar.baz',
        'units': 'meters',
        'type': 'scalar',
        'value': 42,
    }

  def testFlattenTrace_PreservesUnits(self):
    """Tests that _FlattenTrace preserves the units property."""
    trace = self._SampleTrace()
    trace.update({'units': 'ms'})
    row = add_point._FlattenTrace('foo', 'bar', 'bar', trace)
    self.assertEqual(row['units'], 'ms')

  def testFlattenTrace_CoreTraceName(self):
    """Tests that chartname.summary will be flattened to chartname."""
    trace = self._SampleTrace()
    trace.update({'name': 'summary'})
    row = add_point._FlattenTrace('foo', 'bar', 'summary', trace)
    self.assertEqual(row['test'], 'foo/bar')

  def testFlattenTrace_NonSummaryTraceName_SetCorrectly(self):
    """Tests that chart.trace will be flattened to chart/trace."""
    trace = self._SampleTrace()
    trace.update({'name': 'bar.baz'})
    row = add_point._FlattenTrace('foo', 'bar', 'baz', trace)
    self.assertEqual(row['test'], 'foo/bar/baz')

  def testFlattenTrace_ImprovementDirectionCannotBeNone(self):
    """Tests that an improvement_direction must not be None if passed."""
    trace = self._SampleTrace()
    trace.update({'improvement_direction': None})
    with self.assertRaises(add_point.BadRequestError):
      add_point._FlattenTrace('foo', 'bar', 'summary', trace)

  def testFlattenTrace_AddsImprovementDirectionIfPresent(self):
    """Tests that improvement_direction will be respected if present."""
    trace = self._SampleTrace()
    trace.update({'improvement_direction': 'up'})
    row = add_point._FlattenTrace('foo', 'bar', 'summary', trace)
    self.assertTrue(row['higher_is_better'])

  def testFlattenTrace_DoesNotAddImprovementDirectionIfAbsent(self):
    """Tests that no higher_is_better is added if no improvement_direction."""
    row = add_point._FlattenTrace('foo', 'bar', 'summary', self._SampleTrace())
    self.assertNotIn('higher_is_better', row)

  def testFlattenTrace_RejectsBadImprovementDirection(self):
    """Tests that passing a bad improvement_direction will cause an error."""
    trace = self._SampleTrace()
    trace.update({'improvement_direction': 'foo'})
    with self.assertRaises(add_point.BadRequestError):
      add_point._FlattenTrace('foo', 'bar', 'summary', trace)

  def testFlattenTrace_ScalarValue(self):
    """Tests that scalars are flattened to 0-error values."""
    row = add_point._FlattenTrace('foo', 'bar', 'baz', self._SampleTrace())
    self.assertEqual(row['value'], 42)
    self.assertEqual(row['error'], 0)

  def testFlattenTrace_ScalarNoneValue(self):
    """Tests that scalar NoneValue is flattened to NaN."""
    trace = self._SampleTrace()
    trace.update({'value': None, 'none_value_reason': 'reason'})
    row = add_point._FlattenTrace('foo', 'bar', 'baz', trace)
    self.assertTrue(math.isnan(row['value']))
    self.assertEqual(row['error'], 0)

  def testFlattenTrace_ScalarLongValue(self):
    """Tests that scalar values can be longs."""
    trace = self._SampleTrace()
    trace.update({'value': 1000000000L})
    row = add_point._FlattenTrace('foo', 'bar', 'baz', trace)
    self.assertEqual(row['value'], 1000000000L)
    self.assertEqual(row['error'], 0)

  def testFlattenTrace_InvalidScalarValue_RaisesError(self):
    """Tests that scalar NoneValue is flattened to NaN."""
    trace = self._SampleTrace()
    trace.update({'value': [42, 43, 44]})
    with self.assertRaises(add_point.BadRequestError):
      add_point._FlattenTrace('foo', 'bar', 'baz', trace)

  def testFlattenTrace_ListValue(self):
    """Tests that lists are properly flattened to avg/stddev."""
    trace = self._SampleTrace()
    trace.update({
        'type': 'list_of_scalar_values',
        'values': [5, 10, 25, 10, 15],
    })
    row = add_point._FlattenTrace('foo', 'bar', 'baz', trace)
    self.assertAlmostEqual(row['value'], 13)
    self.assertAlmostEqual(row['error'], 6.78232998)

  def testFlattenTrace_ListValue_WithLongs(self):
    """Tests that lists of scalars can include longs."""
    trace = self._SampleTrace()
    trace.update({
        'type': 'list_of_scalar_values',
        'values': [1000000000L, 2000000000L],
    })
    row = add_point._FlattenTrace('foo', 'bar', 'baz', trace)
    self.assertAlmostEqual(row['value'], 1500000000L)
    self.assertAlmostEqual(row['error'], 500000000L)

  def testFlattenTrace_ListValueWithStd(self):
    """Tests that lists with reported std use std as error."""
    trace = self._SampleTrace()
    trace.update({
        'type': 'list_of_scalar_values',
        'values': [5, 10, 25, 10, 15],
        'std': 100,
    })
    row = add_point._FlattenTrace('foo', 'bar', 'baz', trace)
    self.assertNotAlmostEqual(row['error'], 6.78232998)
    self.assertEqual(row['error'], 100)

  def testFlattenTrace_ListNoneValue(self):
    """Tests that LoS NoneValue is flattened to NaN."""
    trace = self._SampleTrace()
    trace.update({
        'type': 'list_of_scalar_values',
        'value': [None],
        'none_value_reason': 'Reason for null value'
    })
    row = add_point._FlattenTrace('foo', 'bar', 'baz', trace)
    self.assertTrue(math.isnan(row['value']))
    self.assertTrue(math.isnan(row['error']))

  def testFlattenTrace_ListNoneValueNoReason_RaisesError(self):
    trace = self._SampleTrace()
    trace.update({
        'type': 'list_of_scalar_values',
        'value': [None],
    })
    with self.assertRaises(add_point.BadRequestError):
      add_point._FlattenTrace('foo', 'bar', 'baz', trace)

  def testFlattenTrace_ListValueNotAList_RaisesError(self):
    trace = self._SampleTrace()
    trace.update({
        'type': 'list_of_scalar_values',
        'values': 42,
    })
    with self.assertRaises(add_point.BadRequestError):
      add_point._FlattenTrace('foo', 'bar', 'baz', trace)

  def testFlattenTrace_ListContainsString_RaisesError(self):
    trace = self._SampleTrace()
    trace.update({
        'type': 'list_of_scalar_values',
        'values': ['-343', 123],
    })
    with self.assertRaises(add_point.BadRequestError):
      add_point._FlattenTrace('foo', 'bar', 'baz', trace)

  def testFlattenTrace_HistogramValue(self):
    """Tests that histograms are yield geommean/stddev as value/error."""
    trace = self._SampleTrace()
    trace.update({
        'type': 'histogram',
        'buckets': [{'low': 1, 'high': 5, 'count': 3},
                    {'low': 4, 'high': 6, 'count': 4}]
    })
    row = add_point._FlattenTrace('foo', 'bar', 'baz', trace)
    self.assertAlmostEqual(row['value'], 4.01690877)
    self.assertAlmostEqual(row['error'], 0.99772482)

  def testFlattenTrace_RespectsIsRefForSameTraceName(self):
    """Tests whether a ref trace that is a chart has the /ref suffix."""
    row = add_point._FlattenTrace(
        'foo', 'bar', 'summary', self._SampleTrace(), is_ref=True)
    self.assertEqual(row['test'], 'foo/bar/ref')

  def testFlattenTrace_RespectsIsRefForDifferentTraceName(self):
    """Tests whether a ref trace that is not a chart has the _ref suffix."""
    row = add_point._FlattenTrace(
        'foo', 'bar', 'baz', self._SampleTrace(), is_ref=True)
    self.assertEqual(row['test'], 'foo/bar/baz_ref')

  def testFlattenTrace_InvalidTraceType(self):
    """Tests whether a ref trace that is not a chart has the _ref suffix."""
    trace = self._SampleTrace()
    trace.update({'type': 'foo'})
    with self.assertRaises(add_point.BadRequestError):
      add_point._FlattenTrace('foo', 'bar', 'baz', trace)

  def testFlattenTrace_SanitizesTraceName(self):
    """Tests whether a trace name with special characters is sanitized."""
    trace = self._SampleTrace()
    trace.update({'page': 'http://example.com'})
    row = add_point._FlattenTrace(
        'foo', 'bar', 'http://example.com', trace)
    self.assertEqual(row['test'], 'foo/bar/http___example.com')

  def testFlattenTrace_FlattensInteractionRecordLabelToFivePartName(self):
    """Tests whether a TIR label will appear between chart and trace name."""
    trace = self._SampleTrace()
    trace.update({
        'name': 'bar',
        'page': 'https://abc.xyz/',
        'tir_label': 'baz'
    })
    row = add_point._FlattenTrace('foo', 'baz@@bar', 'https://abc.xyz/', trace)
    self.assertEqual(row['test'], 'foo/bar/baz/https___abc.xyz_')


if __name__ == '__main__':
  unittest.main()
