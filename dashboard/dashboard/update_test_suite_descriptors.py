# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from google.appengine.ext import ndb

from dashboard import update_test_suites
from dashboard.common import datastore_hooks
from dashboard.common import descriptor
from dashboard.common import namespaced_stored_object
from dashboard.common import request_handler
from dashboard.common import stored_object
from dashboard.common import utils
from dashboard.models import graph_data
from google.appengine.ext import deferred


def CacheKey(test_suite):
  return 'test_suite_descriptor_' + test_suite


def FetchCachedTestSuiteDescriptor(test_suite):
  return namespaced_stored_object.Get(CacheKey(test_suite))


class UpdateTestSuiteDescriptorsHandler(request_handler.RequestHandler):

  def get(self):
    self.post()

  def post(self):
    namespace = datastore_hooks.EXTERNAL
    if self.request.get('internal_only') == 'true':
      datastore_hooks.SetPrivilegedRequest()
      namespace = datastore_hooks.INTERNAL
    UpdateTestSuiteDescriptors(namespace)


def UpdateTestSuiteDescriptors(namespace):
  for suite in update_test_suites.FetchCachedTestSuites2():
    deferred.defer(UpdateDescriptor, suite, namespace)

@ndb.tasklet
def UpdateDescriptor(test_suite, namespace):
  test_path = descriptor.Descriptor(
      test_suite=test_suite, bot='place:holder').ToTestPaths()[0].split('/')

  measurements = set()
  bots = set()
  cases = set()
  # TODO tagmaps

  query = graph_data.TestMetadata.query()
  query = query.filter(graph_data.TestMetadata.suite_name == test_path[2])
  if len(test_path) > 3:
    # test_suite is composite.
    query = query.filter(
        graph_data.TestMetadata.test_part1_name == test_path[3])
  query = query.filter(graph_data.TestMetadata.deprecated == False)
  query = query.filter(graph_data.TestMetadata.has_rows == True)
  keys = yield query.fetch_async(keys_only=True)
  for key in keys:
    test_path = utils.TestPath(key)
    components = test_path.split('/')
    desc = descriptor.Descriptor.FromTestPath(components)
    if components:
      logging.error('Unable to parse %r', test_path)
      return
    bots.add(desc.bot)
    if desc.measurement:
      measurements.add(desc.measurement)
    if desc.test_case:
      cases.add(desc.test_case)

  desc = {
      'measurements': list(sorted(measurements)),
      'bots': list(sorted(bots)),
      'cases': list(sorted(cases)),
  }
  key = namespaced_stored_object.NamespaceKey(
      CacheKey(test_suite), namespace)
  stored_object.Set(key, desc)
