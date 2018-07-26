# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import time

from google.appengine.ext import deferred
from google.appengine.ext import db

from dashboard import update_test_suites
from dashboard.common import datastore_hooks
from dashboard.common import descriptor
from dashboard.common import namespaced_stored_object
from dashboard.common import request_handler
from dashboard.common import stored_object
from dashboard.common import utils
from dashboard.models import graph_data


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
      namespace = datastore_hooks.INTERNAL
    UpdateTestSuiteDescriptors(namespace)


def UpdateTestSuiteDescriptors(namespace):
  key = namespaced_stored_object.NamespaceKey(
      update_test_suites.TEST_SUITES_2_CACHE_KEY, namespace)
  for test_suite in stored_object.Get(key):
    ScheduleUpdateDescriptor(test_suite, namespace)


def ScheduleUpdateDescriptor(test_suite, namespace):
  deferred.defer(_UpdateDescriptor, test_suite, namespace)


DEADLINE_SECONDS = 60 * 9.5


def _UpdateDescriptor(test_suite, namespace, start_cursor=None,
                      measurements=(), bots=(), cases=()):
  deadline = time.time() + DEADLINE_SECONDS
  logging.info('%s %s %d %d %d', test_suite, namespace,
               len(measurements), len(bots), len(cases))
  # This function always runs in the taskqueue as an anonymous user.
  if namespace == datastore_hooks.INTERNAL:
    datastore_hooks.SetPrivilegedRequest()

  test_path = descriptor.Descriptor(
      test_suite=test_suite, bot='place:holder').ToTestPathsSync()[0].split('/')

  measurements = set(measurements)
  bots = set(bots)
  cases = set(cases)
  # TODO(4549) Tagmaps.

  query = graph_data.TestMetadata.query()
  query = query.filter(graph_data.TestMetadata.suite_name == test_path[2])
  if len(test_path) > 3:
    # test_suite is composite.
    query = query.filter(
        graph_data.TestMetadata.test_part1_name == test_path[3])
  query = query.filter(graph_data.TestMetadata.deprecated == False)
  query = query.filter(graph_data.TestMetadata.has_rows == True)

  # Some test suites have more keys than can fit in memory or can be processed
  # in 10 minutes, so use an iterator.
  query_iter = query.iter(
      start_cursor=start_cursor, produce_cursors=True, keys_only=True)

  try:
    for key in query_iter:
      desc = descriptor.Descriptor.FromTestPathSync(utils.TestPath(key))
      bots.add(desc.bot)
      if desc.measurement:
        measurements.add(desc.measurement)
      if desc.test_case:
        cases.add(desc.test_case)
      if time.time() > deadline:
        break
  except db.BadRequestError:
    # Sometimes the iterator runs for a while then throws this. Try, try again.
    logging.warn('BadRequestError caught')

  logging.info('%d measurements, %d bots, %d cases',
               len(measurements), len(bots), len(cases))

  if query_iter.probably_has_next():
    logging.info('continuing')
    deferred.defer(_UpdateDescriptor, test_suite, namespace,
                   query_iter.cursor_before(), measurements, bots, cases)
    return

  desc = {
      'measurements': list(sorted(measurements)),
      'bots': list(sorted(bots)),
      'cases': list(sorted(cases)),
  }
  key = namespaced_stored_object.NamespaceKey(
      CacheKey(test_suite), namespace)
  stored_object.Set(key, desc)
