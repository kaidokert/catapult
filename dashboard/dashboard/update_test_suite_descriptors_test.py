# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock
import unittest
import webapp2
import webtest

from google.appengine.ext import deferred
from google.appengine.ext import ndb

from dashboard import update_test_suites
from dashboard import update_test_suite_descriptors
from dashboard.common import datastore_hooks
from dashboard.common import descriptor
from dashboard.common import namespaced_stored_object
from dashboard.common import stored_object
from dashboard.common import testing_common
from dashboard.common import utils


class UpdateTestSuiteDescriptorsTest(testing_common.TestCase):

  def setUp(self):
    super(UpdateTestSuiteDescriptorsTest, self).setUp()
    app = webapp2.WSGIApplication(
        [('/update_test_suite_descriptors',
          update_test_suite_descriptors.UpdateTestSuiteDescriptorsHandler)])
    self.testapp = webtest.TestApp(app)
    testing_common.SetIsInternalUser('internal@chromium.org', True)
    self.UnsetCurrentUser()
    stored_object.Set(descriptor.PARTIAL_TEST_SUITES_KEY, [
        'TEST_PARTIAL_TEST_SUITE',
    ])
    stored_object.Set(descriptor.COMPOSITE_TEST_SUITES_KEY, [
        'TEST_PARTIAL_TEST_SUITE:COMPOSITE',
    ])
    stored_object.Set(descriptor.GROUPABLE_TEST_SUITE_PREFIXES_KEY, [
        'TEST_GROUPABLE%',
    ])
    def DontDefer(func, *a, **kw):
      result = func(*a, **kw)
      if isinstance(result, ndb.Future):
        result = result.get_result()
    defer_patch = mock.patch.object(deferred, 'defer', DontDefer)
    defer_patch.start()
    self.addCleanup(defer_patch.stop)

  def testInternal(self):
    internal_key = namespaced_stored_object.NamespaceKey(
        update_test_suites.TEST_SUITES_2_CACHE_KEY, datastore_hooks.INTERNAL)
    stored_object.Set(internal_key, ['internal'])
    testing_common.AddTests(
        ['master'],
        ['bot'],
        {
            'internal': {
                'measurement': {
                    'test_case': {},
                },
            },
        })
    test = utils.TestKey('master/bot/internal/measurement/test_case').get()
    test.has_rows = True
    test.put()

    self.testapp.post('/update_test_suite_descriptors?internal_only=true')
    expected = {
        'measurements': ['measurement'],
        'bots': ['master:bot'],
        'cases': ['test_case'],
    }
    self.SetCurrentUser('internal@chromium.org')
    actual = update_test_suite_descriptors.FetchCachedTestSuiteDescriptor(
        'internal')
    self.assertEqual(expected, actual)

  def testComposite(self):
    external_key = namespaced_stored_object.NamespaceKey(
        update_test_suites.TEST_SUITES_2_CACHE_KEY, datastore_hooks.EXTERNAL)
    stored_object.Set(external_key, ['TEST_PARTIAL_TEST_SUITE:COMPOSITE'])
    testing_common.AddTests(
        ['master'],
        ['bot'],
        {
            'TEST_PARTIAL_TEST_SUITE': {
                'COMPOSITE': {
                    'measurement': {
                        'test_case': {},
                    },
                },
            },
        })
    test = utils.TestKey('master/bot/TEST_PARTIAL_TEST_SUITE/COMPOSITE/' +
                         'measurement/test_case').get()
    test.has_rows = True
    test.put()

    self.testapp.post('/update_test_suite_descriptors')
    expected = {
        'measurements': ['measurement'],
        'bots': ['master:bot'],
        'cases': ['test_case'],
    }
    actual = update_test_suite_descriptors.FetchCachedTestSuiteDescriptor(
        'TEST_PARTIAL_TEST_SUITE:COMPOSITE')
    self.assertEqual(expected, actual)

  def testTagMap(self):
    pass  # TODO

  def testUnparsed(self):
    external_key = namespaced_stored_object.NamespaceKey(
        update_test_suites.TEST_SUITES_2_CACHE_KEY, datastore_hooks.EXTERNAL)
    stored_object.Set(external_key, ['unparsed'])
    testing_common.AddTests(
        ['master'],
        ['bot'],
        {
            'unparsed': {
                'a': {
                    'b': {
                        'c': {},
                    },
                },
            },
        })
    test = utils.TestKey('master/bot/unparsed/a/b/c').get()
    test.has_rows = True
    test.put()

    self.testapp.post('/update_test_suite_descriptors')
    actual = update_test_suite_descriptors.FetchCachedTestSuiteDescriptor(
        'unparsed')
    self.assertEqual(None, actual)


if __name__ == '__main__':
  unittest.main()
