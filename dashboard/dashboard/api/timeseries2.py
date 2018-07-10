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


DIAGNOSTICS_QUERY_LIMIT = 10000
HISTOGRAMS_QUERY_LIMIT = 10000
ROWS_QUERY_LIMIT = 20000
COLUMNS_REQUIRING_ROWS = {'avg', 'std', 'timestamp', 'revisions'}


class Timeseries2Handler(api_request_handler.ApiRequestHandler):

  def __init__(self, request, response):
    self.initialize(request, response)
    self._descriptor = None
    self._min_revision = None
    self._max_revision = None
    self._columns = []
    self._unsuffixed_test_metadata_keys = []
    self._test_keys = []
    self._units = None
    self._improvement_direction = None
    self._data = {}

  def AuthorizedPost(self):
    self._descriptor = descriptor.Descriptor(
        test_suite=self.request.get('test_suite'),
        measurement=self.request.get('measurement'),
        bot=self.request.get('bot'),
        test_case=self.request.get('test_case'),
        statistic=None,
        build_type=self.request.get('build_type'))
    self._min_revision = self.request.get('min_rev')
    self._min_revision = int(self._min_revision) if self._min_revision else None
    self._max_revision = self.request.get('max_rev')
    self._max_revision = int(self._max_revision) if self._max_revision else None
    self._columns = self.request.get('columns').split(',')
    return self.Query()

  def Query(self):
    # Always need to get tests even if the caller doesn't need units and
    # improvement_direction because Row doesn't have internal_only.
    # Use tasklets so that they can process the data as it arrives.
    self._CreateTestKeys()
    futures = [self._QueryTests()]
    if COLUMNS_REQUIRING_ROWS.intersection(self._columns):
      futures.append(self._QueryRows())
    if 'alert' in self._columns:
      futures.append(self._QueryAlerts())
    if 'histogram' in self._columns:
      futures.append(self._QueryHistograms())
    if 'diagnostics' in self._columns:
      futures.append(self._QueryDiagnostics())
    try:
      ndb.Future.wait_all(futures)
      for future in futures:
        # Propagate exceptions from the tasklets.
        future.get_result()
    except AssertionError:
      # The caller has requested internal-only data but is not authorized.
      raise api_request_handler.NotFoundError
    return {
        'units': self._units,
        'improvement_direction': self._improvement_direction,
        'data': [[datum.get(col) for col in self._columns]
                 for _, datum in sorted(self._data.iteritems())],
    }

  def _Datum(self, revision):
    return self._data.setdefault(revision, {'revision': revision})

  def _CreateTestKeys(self):
    desc = self._descriptor.Clone()

    desc.statistic = None
    unsuffixed_test_paths = desc.ToTestPaths()
    self._unsuffixed_test_metadata_keys = [
        utils.TestMetadataKey(path) for path in unsuffixed_test_paths]

    test_paths = []
    for statistic in descriptor.STATISTICS:
      if statistic in self._columns:
        desc.statistic = statistic
        test_paths.extend(desc.ToTestPaths())

    test_metadata_keys = [utils.TestMetadataKey(path) for path in test_paths]
    test_metadata_keys.extend(self._unsuffixed_test_metadata_keys)
    test_paths.extend(unsuffixed_test_paths)

    test_old_keys = [utils.OldStyleTestKey(path) for path in test_paths]
    self._test_keys = test_old_keys + test_metadata_keys

  @ndb.tasklet
  def _QueryTests(self):
    tests = yield [key.get_async() for key in self._test_keys]
    tests = [test for test in tests if test]
    if not tests:
      raise api_request_handler.NotFoundError

    improvement_direction = None
    for test in tests:
      test_desc = descriptor.Descriptor.FromTestPath(utils.TestPath(test.key))
      # The unit for 'count' statistics is trivially always 'count'. Callers
      # certainly want the units of the measurement, which is the same as the
      # units of the 'avg' and 'std' statistics.
      if self._units is None or test_desc.statistic != 'count':
        self._units = test.units
        improvement_direction = test.improvement_direction

    if improvement_direction == anomaly.DOWN:
      self._improvement_direction = 'down'
    elif improvement_direction == anomaly.UP:
      self._improvement_direction = 'up'
    else:
      self._improvement_direction = None

  @ndb.tasklet
  def _QueryRows(self):
    limit = ROWS_QUERY_LIMIT
    projection = None
    if 'std' not in self._columns and 'revisions' not in self._columns:
      projection = ['revision', 'value']
      if 'timestamp' in self._columns:
        projection.append('timestamp')
      limit = None

    row_futures = []
    for test_key in self._test_keys:
      query = graph_data.Row.query(projection=projection)
      query = query.filter(graph_data.Row.parent_test == test_key)
      if self._min_revision:
        query = query.filter(graph_data.Row.revision >= self._min_revision)
      if self._max_revision:
        query = query.filter(graph_data.Row.revision <= self._max_revision)
      row_futures.append(query.fetch_async(limit))

    for timeseries in (yield row_futures):
      if not timeseries:
        continue
      test_desc = descriptor.Descriptor.FromTestPath(
          utils.TestPath(timeseries[0].parent_test))
      for row in timeseries:
        datum = self._Datum(row.revision)
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
        if 'revisions' in self._columns:
          datum['revisions'] = {
              attr: value for attr, value in row.to_dict().iteritems()
              if attr.startswith('r_')}

  @ndb.tasklet
  def _QueryAlerts(self):
    anomalies, _, _ = yield anomaly.Anomaly.QueryAsync(
        test_keys=self._test_keys,
        max_start_revision=self._max_revision,
        min_end_revision=self._min_revision)
    for alert in anomalies:
      # TODO(benjhayden) end_revision or start_revision?
      datum = self._Datum(alert.end_revision)
      # TODO(benjhayden) bisect_status
      datum['alert'] = alerts.GetAnomalyDict(alert)

  @ndb.tasklet
  def _QueryHistograms(self):
    query = histogram.Histogram.query(histogram.Histogram.test.IN(
        self._unsuffixed_test_metadata_keys))
    if self._min_revision:
      query = query.filter(
          histogram.Histogram.revision >= self._min_revision)
    if self._max_revision:
      query = query.filter(
          histogram.Histogram.revision <= self._max_revision)
    for hist in (yield query.fetch_async(HISTOGRAMS_QUERY_LIMIT)):
      self._Datum(hist.revision)['histogram'] = hist.data

  @ndb.tasklet
  def _QueryDiagnostics(self):
    query = histogram.SparseDiagnostic.query(histogram.SparseDiagnostic.test.IN(
        self._unsuffixed_test_metadata_keys))
    if self._min_revision:
      query = query.filter(
          histogram.SparseDiagnostic.start_revision >= self._min_revision)
    if self._max_revision:
      query = query.filter(
          histogram.SparseDiagnostic.start_revision <= self._max_revision)
    for diag in (yield query.fetch_async(DIAGNOSTICS_QUERY_LIMIT)):
      # TODO end_revision or start_revision?
      datum = self._Datum(diag.start_revision)
      datum_diags = datum.setdefault('diagnostics', {})
      datum_diags[diag.name] = diag.data
