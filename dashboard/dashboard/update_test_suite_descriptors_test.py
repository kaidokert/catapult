# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import webapp2
import unittest

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
    handler = update_test_suite_descriptors.UpdateTestSuiteDescriptorsHandler
    self.SetUpApp([('/update_test_suite_descriptors', handler)])
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
    descriptor.Descriptor.ResetMemoizedConfigurationForTesting()

  def testUpdateDescriptor(self):
    # Calling UpdateDescriptor() directly as an internal user should still
    # filter out internal_only TestMetadata.

    external_key = namespaced_stored_object.NamespaceKey(
        update_test_suites.TEST_SUITES_2_CACHE_KEY, datastore_hooks.EXTERNAL)
    stored_object.Set(external_key, ['suite'])
    testing_common.AddTests(
        ['master'],
        ['external', 'internal'],
        {
            'suite': {
                'measurement': {
                    'test_case': {},
                },
            },
        })
    test = utils.TestKey('master/internal/suite/measurement/test_case').get()
    test.has_rows = True
    test.internal_only = True
    test.put()
    test = utils.TestKey('master/external/suite/measurement/test_case').get()
    test.has_rows = True
    test.put()

    self.SetCurrentUser('internal@chromium.org')
    update_test_suite_descriptors.UpdateDescriptor(
        'suite', datastore_hooks.EXTERNAL)

    expected = {
        'measurements': ['measurement'],
        'bots': ['master:external'],
        'cases': ['test_case'],
    }
    self.SetCurrentUser('external@chromium.org')
    actual = update_test_suite_descriptors.FetchCachedTestSuiteDescriptor(
        'suite')
    self.assertEqual(expected, actual)

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
    test.internal_only = True
    test.put()

    self.Post('/update_test_suite_descriptors?internal_only=true')

    # deferred.Defer() packages up the function call and arguments, not changes
    # to global state like SetPrivilegedRequest, so set privileged=False as the
    # taskqueue does, and test that UpdateDescriptor sets it back to True so
    # that it gets the internal TestMetadata.
    class FakeRequest(object):
      def __init__(self):
        self.registry = {'privileged': False}
    webapp2._local.request = FakeRequest()
    self.ExecuteDeferredTasks('default')

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

    self.Post('/update_test_suite_descriptors')
    self.ExecuteDeferredTasks('default')
    expected = {
        'measurements': ['measurement'],
        'bots': ['master:bot'],
        'cases': ['test_case'],
    }
    actual = update_test_suite_descriptors.FetchCachedTestSuiteDescriptor(
        'TEST_PARTIAL_TEST_SUITE:COMPOSITE')
    self.assertEqual(expected, actual)

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

    self.Post('/update_test_suite_descriptors')
    with self.assertRaises(ValueError):
      self.ExecuteDeferredTasks('default')
    actual = update_test_suite_descriptors.FetchCachedTestSuiteDescriptor(
        'unparsed')
    self.assertEqual(None, actual)


if __name__ == '__main__':
  unittest.main()
