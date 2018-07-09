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


class Timeseries2Handler(api_request_handler.ApiRequestHandler):

  def AuthorizedPost(self):
    desc = descriptor.Descriptor(
        test_suite=self.request.get('test_suite'),
        measurement=self.request.get('measurement'),
        bot=self.request.get('bot'),
        test_case=self.request.get('test_case'),
        statistic=None,
        build_type=self.request.get('build_type'))
    min_rev = self.request.get('min_rev')
    min_rev = int(min_rev) if min_rev else None
    max_rev = self.request.get('max_rev')
    max_rev = int(max_rev) if max_rev else None
    columns = self.request.get('columns').split(',')

    return Fetch(desc, min_rev, max_rev, columns)


def _GetTests(desc, columns):
  desc = desc.Clone()

  desc.statistic = None
  unsuffixed_test_paths = desc.ToTestPaths()
  unsuffixed_test_metadata_keys = [
      utils.TestMetadataKey(path) for path in unsuffixed_test_paths]

  test_paths = []
  for statistic in descriptor.STATISTICS:
    if statistic in columns:
      desc.statistic = statistic
      test_paths.extend(desc.ToTestPaths())

  test_metadata_keys = [utils.TestMetadataKey(path) for path in test_paths]
  test_metadata_keys.extend(unsuffixed_test_metadata_keys)
  test_paths.extend(unsuffixed_test_paths)

  # TODO(benjhayden): Can we ever remove old style test keys?
  test_old_keys = [utils.OldStyleTestKey(path) for path in test_paths]
  test_keys = test_old_keys + test_metadata_keys

  test_futures = [key.get_async() for key in test_keys]
  return (unsuffixed_test_metadata_keys, test_keys, test_futures)


def _GetRows(test_keys, min_rev, max_rev, columns):
  if not set(columns).intersection({'avg', 'std', 'timestamp', 'revisions'}):
    return []

  limit = 20000
  projection = None
  if 'std' not in columns and 'revisions' not in columns:
    projection = ['revision', 'value']
    if 'timestamp' in columns:
      projection.append('timestamp')
    limit = None

  row_futures = []
  for test_key in test_keys:
    query = graph_data.Row.query(projection=projection)
    query = query.filter(graph_data.Row.parent_test == test_key)
    if min_rev:
      query = query.filter(graph_data.Row.revision >= min_rev)
    if max_rev:
      query = query.filter(graph_data.Row.revision <= max_rev)
    row_futures.append(query.fetch_async(limit))
  return row_futures


def _GetAlerts(test_keys, min_rev, max_rev, columns):
  if 'alert' not in columns:
    return None

  return anomaly.Anomaly.QueryAsync(
      test_keys=test_keys, max_start_revision=max_rev, min_end_revision=min_rev)


def _GetHistograms(unsuffixed_test_metadata_keys, min_rev, max_rev, columns):
  if 'histogram' not in columns:
    return None

  histogram_query = histogram.Histogram.query(histogram.Histogram.test.IN(
      unsuffixed_test_metadata_keys))
  if min_rev:
    histogram_query = histogram_query.filter(
        histogram.Histogram.revision >= min_rev)
  if max_rev:
    histogram_query = histogram_query.filter(
        histogram.Histogram.revision <= max_rev)
  return histogram_query.fetch_async(10000)


def _GetDiagnostics(unsuffixed_test_metadata_keys, min_rev, max_rev, columns):
  if 'diagnostics' not in columns:
    return None

  diagnostic_query = histogram.SparseDiagnostic.query(
      histogram.SparseDiagnostic.test.IN(unsuffixed_test_metadata_keys))
  if min_rev:
    diagnostic_query = diagnostic_query.filter(
        histogram.SparseDiagnostic.start_revision >= min_rev)
  elif max_rev:
    diagnostic_query = diagnostic_query.filter(
        histogram.SparseDiagnostic.start_revision <= max_rev)
  return diagnostic_query.fetch_async(10000)


def _GetUnits(tests):
  units = None
  improvement_direction = None
  for test in tests:
    test_desc = descriptor.Descriptor.FromTestPath(utils.TestPath(test.key))
    # TODO comment count exception
    if units is None or test_desc.statistic != 'count':
      units = test.units
      improvement_direction = test.improvement_direction
  if improvement_direction == anomaly.DOWN:
    improvement_direction = 'down'
  elif improvement_direction == anomaly.UP:
    improvement_direction = 'up'
  else:
    improvement_direction = None
  return units, improvement_direction


def _MergeRows(data_by_revision, row_futures, columns):
  for row_future in row_futures:
    rows = row_future.get_result()
    if not rows:
      continue
    test_desc = descriptor.Descriptor.FromTestPath(
        utils.TestPath(rows[0].parent_test))
    for row in rows:
      # TODO check if statistic is in row.parent_test
      datum = data_by_revision.setdefault(row.revision, {
          'revision': row.revision})
      if test_desc.statistic in [None, 'avg']:
        datum['avg'] = round(row.value, 6)
      elif test_desc.statistic == 'std':
        datum['std'] = round(row.value, 6)
      elif test_desc.statistic == 'count':
        datum['count'] = round(row.value, 6)
      if row.error:
        datum['std'] = round(row.error, 6)
      if hasattr(row, 'd_count'):
        datum['count'] = round(row.d_count, 6)
      datum['timestamp'] = row.timestamp.isoformat()
      if 'revisions' in columns:
        datum['revisions'] = {
            attr: value for attr, value in row.to_dict().iteritems()
            if attr.startswith('r_')}


def _MergeAlerts(data_by_revision, anomaly_future):
  if not anomaly_future:
    return

  for alert in anomaly_future.get_result()[0]:
    # TODO end_revision or start_revision?
    datum = data_by_revision.setdefault(alert.end_revision, {
        'revision': alert.end_revision})
    # TODO bisect_status
    datum['alert'] = alerts.GetAnomalyDict(alert)


def _MergeHistograms(data_by_revision, histogram_future):
  if not histogram_future:
    return

  for hist in histogram_future.get_result():
    datum = data_by_revision.setdefault(hist.revision, {
        'revision': hist.revision})
    datum['histogram'] = hist.data


def _MergeDiagnostics(data_by_revision, min_rev, max_rev, diagnostic_future):
  if not diagnostic_future:
    return

  for diag in diagnostic_future.get_result():
    # TODO end_revision or start_revision?
    if min_rev and diag.start_revision < min_rev:
      continue
    if max_rev and diag.start_revision > max_rev:
      continue
    datum = data_by_revision.setdefault(diag.start_revision, {
        'revision': diag.start_revision})
    datum_diags = datum.setdefault('diagnostics', {})
    datum_diags[diag.name] = diag.data


def Fetch(desc, min_rev, max_rev, columns):
  # Construct Futures.
  (unsuffixed_test_metadata_keys, test_keys, test_futures) = _GetTests(
      desc, columns)
  row_futures = _GetRows(test_keys, min_rev, max_rev, columns)
  anomaly_future = _GetAlerts(test_keys, min_rev, max_rev, columns)
  histogram_future = _GetHistograms(
      unsuffixed_test_metadata_keys, min_rev, max_rev, columns)
  diagnostic_future = _GetDiagnostics(
      unsuffixed_test_metadata_keys, min_rev, max_rev, columns)

  # Collect Futures.
  futures = []
  futures.extend(test_futures)
  futures.extend(row_futures)
  if anomaly_future:
    futures.append(anomaly_future)
  if histogram_future:
    futures.append(histogram_future)
  if diagnostic_future:
    futures.append(diagnostic_future)

  try:
    ndb.Future.wait_all(futures)
  except AssertionError:
    # The caller has requested internal-only data but is not authorized.
    raise api_request_handler.NotFoundError

  # Collect tests.
  tests = []
  for test_future in test_futures:
    test = test_future.get_result()
    if test:
      tests.append(test)
  if not tests:
    raise api_request_handler.NotFoundError

  units, improvement_direction = _GetUnits(tests)

  # Merge data from various Futures into single timeseries.
  data_by_revision = {}
  _MergeRows(data_by_revision, row_futures, columns)
  _MergeAlerts(data_by_revision, anomaly_future)
  _MergeHistograms(data_by_revision, histogram_future)
  _MergeDiagnostics(data_by_revision, min_rev, max_rev, diagnostic_future)
  data = [[datum.get(col) for col in columns]
          for _, datum in sorted(data_by_revision.iteritems())]

  return {
      'units': units,
      'improvement_direction': improvement_direction,
      'data': data,
  }
