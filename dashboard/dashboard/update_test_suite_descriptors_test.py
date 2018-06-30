# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest
import webapp2
import webtest

from dashboard import update_test_suites
from dashboard import update_test_suite_descriptors
from dashboard.common import datastore_hooks
from dashboard.common import descriptor
from dashboard.common import namespaced_stored_object
from dashboard.common import stored_object
from dashboard.common import testing_common


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
    external_key = namespaced_stored_object.NamespaceKey(
        update_test_suites.TEST_SUITES_2_CACHE_KEY, datastore_hooks.EXTERNAL)
    stored_object.Set(external_key, ['external'])
    internal_key = namespaced_stored_object.NamespaceKey(
        update_test_suites.TEST_SUITES_2_CACHE_KEY, datastore_hooks.INTERNAL)
    stored_object.Set(internal_key, ['external', 'internal'])

  def testPartialTestSuites(self):
    testing_common.AddTests(
        ['master'],
        ['bot'],
        {
            'TEST_PARTIAL_TEST_SUITE': {
                'COMPOSITE': {
                    'measurement': {},
                },
            },
        })
    self.testapp.post('/update_test_suite_descriptors')
    self.assertEqual(
        {},
        update_test_suite_descriptors.FetchCachedTestSuiteDescriptors(
            'TEST_PARTIAL_TEST_SUITE:COMPOSITE'))


if __name__ == '__main__':
  unittest.main()
