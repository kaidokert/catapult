# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from google.appengine.ext import ndb

from dashboard import alerts
from dashboard.api import api_request_handler
from dashboard.common import descriptor
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import graph_data
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
    min_rev = self.request.get('min_rev')
    min_rev = int(min_rev) if min_rev else None
    max_rev = self.request.get('max_rev')
    max_rev = int(max_rev) if max_rev else None
    columns = self.request.get('columns').split(',')

    return Fetch(desc, min_rev, max_rev, columns)


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
  test_metadata_keys = [utils.TestMetadataKey(path) for path in test_paths]
  test_old_keys = [utils.OldStyleTestKey(path) for path in test_paths]
  test_keys = test_old_keys + test_metadata_keys
  test_futures = [key.get_async() for key in test_keys]
  futures += test_futures

  def FilterRevision(query, cls):
    if min_rev:
      query = query.filter(cls.revision >= min_rev)
    if max_rev:
      query = query.filter(cls.revision <= max_rev)
    return query

  if set(columns).intersection({'avg', 'std', 'timestamp', 'revisions'}):
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
        histogram.Histogram.test.IN(test_metadata_keys))
    histogram_query = FilterRevision(histogram_query, histogram.Histogram)
    histogram_future = histogram_query.fetch_async(MAX_POINTS)
    futures.append(histogram_future)

  if 'diagnostics' in columns:
    diagnostic_query = histogram.SparseDiagnostic.query(
        histogram.SparseDiagnostic.test.IN(test_metadata_keys))
    diagnostic_query = FilterRevision(
        diagnostic_query, histogram.SparseDiagnostic)
    diagnostic_future = diagnostic_query.fetch_async(MAX_POINTS)
    futures.append(diagnostic_future)

  ndb.Future.wait_all(futures)

  tests = [test_future.get_result() for test_future in test_futures]
  tests = [test for test in tests if test]

  units = None
  improvement_direction = None
  for test in tests:
    test_desc = descriptor.Descriptor.FromTestPath(utils.TestPath(test.key))
    if test_desc.statistic == desc.statistic or units is None:
      units = test.units
      improvement_direction = test.improvement_direction

  data_by_revision = {}

  if row_future:
    for row in row_future.get_result():
      # TODO check if statistic is in row.parent_test
      datum = data_by_revision.setdefault(row.revision, {
          'revision': row.revision})
      datum['avg'] = round(row.value, 6)
      if row.error:
        datum['std'] = round(row.error, 6)
      datum['timestamp'] = row.timestamp.isoformat()
      if 'revisions' in columns:
        datum['revisions'] = {attr: getattr(row, attr)
                              for attr in dir(row) if attr.startswith('r_')}

  if anomaly_future:
    for alert in anomaly_future.get_result()[0]:
      # TODO end_revision or start_revision?
      datum = data_by_revision.setdefault(alert.end_revision, {
          'revision': alert.end_revision})
      # TODO bisect_status
      datum['alert'] = alerts.GetAnomalyDict(alert)

  if histogram_future:
    for hist in histogram_future.get_result():
      datum = data_by_revision.setdefault(hist.revision, {
          'revision': hist.revision})
      datum['histogram'] = hist.data

  if diagnostic_future:
    for diag in diagnostic_future.get_result():
      # TODO end_revision or start_revision?
      datum = data_by_revision.setdefault(diag.start_revision, {
          'revision': diag.start_revision})
      datum_diags = datum.setdefault('diagnostics', {})
      datum_diags[diag.name] = diag.data

  data_by_revision = data_by_revision.items()
  data_by_revision.sort()
  data = [
      [datum.get(col) for col in columns]
      for _, datum in data_by_revision
  ]

  return {
      'units': units,
      'improvement_direction': improvement_direction,
      'data': data,
  }
