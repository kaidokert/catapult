# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from google.appengine.ext import ndb

from dashboard.api import api_request_handler
from dashboard.common import descriptor
from dashboard.common import utils
from dashboard.models import graph_data
from dashboard.models import anomaly
from dashboard.models import histogram


MAX_POINTS = 20000


class Timeseries2Handler(api_request_handler.ApiRequestHandler):

  def AuthorizedPost(self):
    desc = descriptor.Descriptor(
        self.request.get('test_suite'),
        self.request.get('measurement'),
        self.request.get('bot'),
        self.request.get('test_case'),
        self.request.get('statistic'),
        self.request.get('build_type'))
    min_rev = self.request.get('minRevision')
    min_rev = int(min_rev) if min_rev else None
    max_rev = self.request.get('maxRevision')
    max_rev = int(max_rev) if max_rev else None
    columns = self.request.get('columns').split(',')

    return Fetch(desc, min_rev, max_rev, columns)


@ndb.synctasklet
def Fetch(desc, min_rev, max_rev, columns):
  futures = []
  row_future = None
  anomaly_future = None
  histogram_future = None
  diagnostic_future = None

  test_paths = desc.ToTestPaths()
  if desc.statistic:
    clone = desc.Clone()
    clone.statistic = None
    test_paths += clone.ToTestPaths()
  test_keys = [style(path)
               for path in test_paths
               for style in [utils.OldStyleTestKey, utils.TestMetadataKey]]
  test_futures = [key.get_async() for key in test_keys]
  futures += test_futures

  def FilterRevision(query, cls):
    if min_rev:
      query = query.filter(cls.revision >= min_rev)
    if max_rev:
      query = query.filter(cls.revision >= max_rev)
    return query

  if set(columns).intersection({'avg', 'std'}):
    row_query = graph_data.Row.query(graph_data.Row.parent_test.IN(test_keys))
    # TODO projection
    row_query = FilterRevision(row_query, graph_data.Row)
    row_future = row_query.fetch_async(MAX_POINTS)
    futures.append(row_future)

  if 'alert' in columns:
    anomaly_future = anomaly.Anomaly.QueryAsync(
        test_keys=test_keys,
        min_start_revision=max_rev,
        min_end_revision=min_rev)
    futures.append(anomaly_future)

  if 'histogram' in columns:
    histogram_query = histogram.Histogram.query(
        histogram.Histogram.test.IN(test_keys))
    histogram_query = FilterRevision(histogram_query, histogram.Histogram)
    histogram_future = histogram_query.fetch_async(MAX_POINTS)
    futures.append(histogram_future)

  if 'diagnostics' in columns:
    diagnostic_query = histogram.SparseDiagnostic.query(
        histogram.SparseDiagnostic.test.IN(test_keys))
    diagnostic_query = FilterRevision(
        diagnostic_query, histogram.SparseDiagnostic)
    diagnostic_future = diagnostic_query.fetch_async(MAX_POINTS)
    futures.append(diagnostic_future)

  yield futures

  tests = [test_future.get_result() for test_future in test_futures]
  tests = [test for test in tests if test]

  units = None
  improvement_direction = None
  for test in tests:
    test_desc = descriptor.Descriptor.FromTestPath(utils.TestPath(test.key()))
    if test_desc.statistic == desc.statistic or units is None:
      units = test.units
      improvement_direction = test.improvement_direction

  data = []
  # TODO

  return {
      'units': units,
      'improvement_direction': improvement_direction,
      'data': data,
  }
