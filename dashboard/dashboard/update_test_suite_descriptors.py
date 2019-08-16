# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import logging

from google.appengine.ext import deferred
from google.appengine.ext import ndb

from dashboard import update_test_suites
from dashboard.common import datastore_hooks
from dashboard.common import namespaced_stored_object
from dashboard.common import request_handler
from dashboard.common import stored_object
from dashboard.common import utils
from dashboard.models import graph_data
from dashboard.models import histogram
from tracing.value.diagnostics import reserved_infos
from tracing.value.diagnostics import generic_set


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


def _QueryTestSuite(test_suite):
  query = graph_data.TestMetadata.query()
  query = query.filter(graph_data.TestMetadata.suite_name == test_suite)
  query = query.filter(graph_data.TestMetadata.deprecated == False)
  query = query.filter(graph_data.TestMetadata.has_rows == True)
  return query


@ndb.tasklet
def _QueryCaseTags(test_path, case):
  data_by_name = yield histogram.SparseDiagnostic.GetMostRecentDataByNamesAsync(
      utils.TestKey(test_path), [reserved_infos.STORY_TAGS.name])
  data = data_by_name.get(reserved_infos.STORY_TAGS.name)
  tags = list(generic_set.GenericSet.FromDict(data)) if data else []
  raise ndb.Return((case, tags))


def _CollectCaseTags(futures, case_tags):
  ndb.Future.wait_all(futures)
  for future in futures:
    case, tags = future.get_result()
    for tag in tags:
      case_tags.setdefault(tag, []).append(case)


TESTS_TO_FETCH = 5000


def _UpdateDescriptor(test_suite, namespace, start_cursor=None,
                      measurements=(), bots=(), cases=(), case_tags=None):
  logging.info('%s %s %d %d %d', test_suite, namespace,
               len(measurements), len(bots), len(cases))
  # This function always runs in the taskqueue as an anonymous user.
  if namespace == datastore_hooks.INTERNAL:
    datastore_hooks.SetPrivilegedRequest()

  measurements = set(measurements)
  bots = set(bots)
  cases = set(cases)
  case_tags = case_tags or {}
  tags_futures = []

  # Some test suites have more keys than can fit in memory or can be processed
  # in 10 minutes, so use an iterator instead of a page limit.
  tests, next_cursor, more = _QueryTestSuite(test_suite).fetch_page(
      TESTS_TO_FETCH, start_cursor=start_cursor,
      use_cache=False, use_memcache=False)

  for test in tests:
    tir_label, measurement, story = utils.ParseTelemetryMetricParts(
        test.test_path)
    if not any((tir_label, measurement, story)):
      logging.error('Parsing error encounted: %s', test.test_path)

    bots.add(test.bot_name)

    if test.unescaped_story_name:
      story = test.unescaped_story_name

    if measurement:
      measurements.add(measurement)

    if story:
      if story not in cases:
        cases.add(story)
        tags_futures.append(_QueryCaseTags(test.test_path, story))

  _CollectCaseTags(tags_futures, case_tags)

  logging.info('%d keys, %d measurements, %d bots, %d cases, %d tags',
               len(tests), len(measurements), len(bots), len(cases),
               len(case_tags))

  if more:
    logging.info('continuing')
    deferred.defer(_UpdateDescriptor, test_suite, namespace,
                   next_cursor, measurements, bots, cases,
                   case_tags)
    return

  desc = {
      'measurements': list(sorted(measurements)),
      'bots': list(sorted(bots)),
      'cases': list(sorted(cases)),
      'caseTags': {tag: sorted(cases) for tag, cases in list(case_tags.items())}
  }

  key = namespaced_stored_object.NamespaceKey(
      CacheKey(test_suite), namespace)
  stored_object.Set(key, desc)
