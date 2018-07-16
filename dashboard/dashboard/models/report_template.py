# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from google.appengine.ext import ndb

from dashboard.common import descriptor
from dashboard.common import timing
from dashboard.common import utils
from dashboard.models import graph_data
from dashboard.models import internal_only_model
from tracing.value import histogram as histogram_module


RunningStatistics = histogram_module.RunningStatistics


class ReportTemplate(internal_only_model.InternalOnlyModel):
  internal_only = ndb.BooleanProperty(indexed=True, default=False)
  name = ndb.StringProperty()
  modified = ndb.DateTimeProperty(indexed=False, auto_now=True)
  owners = ndb.StringProperty(repeated=True)
  template = ndb.JsonProperty()


STATIC_TEMPLATES = []


def Static(internal_only, template_id, name, modified):
  def Decorator(handler):
    handler.template = ReportTemplate(
        internal_only=internal_only,
        id=template_id,
        name=name,
        modified=modified)
    STATIC_TEMPLATES.append(handler)
    return handler
  return Decorator


def List():
  with timing.WallTimeLogger('List'), timing.CpuTimeLogger('List'):
    templates = ReportTemplate.query().fetch()
    templates += [
        handler.template for handler in STATIC_TEMPLATES
        if (not handler.template.internal_only) or utils.IsInternalUser()]
    templates = [
        {
            'id': template.key.id(),
            'name': template.name,
            'modified': template.modified.isoformat(),
        }
        for template in templates]
    return sorted(templates, key=lambda d: d['name'])


def PutTemplate(template_id, name, owners, template):
  email = utils.GetEmail()
  if email is None:
    raise ValueError
  if template_id is None:
    entity = ReportTemplate()
  else:
    for handler in STATIC_TEMPLATES:
      if handler.template.key.id() == template_id:
        raise ValueError
    try:
      entity = ndb.Key('ReportTemplate', template_id).get()
    except AssertionError:
      raise ValueError
    if not entity or email not in entity.owners:
      raise ValueError

  entity.name = name
  entity.owners = owners
  entity.template = template
  entity.put()


def GetReport(template_id, revisions):
  with timing.WallTimeLogger('GetReport'), timing.CpuTimeLogger('GetReport'):
    try:
      template = ndb.Key('ReportTemplate', template_id).get()
    except AssertionError:
      return None
    result = {}
    if template:
      result['report'] = ReportQuery(template.template, revisions).FetchSync()
    else:
      for handler in STATIC_TEMPLATES:
        if handler.template.key.id() == template_id:
          if handler.template.internal_only and not utils.IsInternalUser():
            return None
          template = handler.template
          report = handler(revisions)
          if isinstance(report, ReportQuery):
            report = report.FetchSync()
          result['report'] = report
          break
      if template is None:
        return None

    result['id'] = template.key.id()
    result['name'] = template.name
    result['internal'] = template.internal_only
    return result


class ReportQuery(object):
  """Take a template and revisions. Return a report.

  Templates look like this: {
    statistics: ['avg', 'std'],
    rows: [
      {label, testSuites, measurement, bots, testCases},
    ],
  }

  Reports look like this: {
    statistics: ['avg', 'std'],
    rows: [
      {
        label, testSuites, measurement, bots, testCases, units,
        improvement_direction,
        data: {
          [revision]: {
            statistics: RunningStatisticsDict,
            descriptors: [{suite, bot, case, revision}],
          },
        },
      },
      ...
    ],
  }
  """

  def __init__(self, template, revisions):
    # Clone the template so that we can set table_row['data'] and the client
    # still gets to see the statistics, row testSuites, measurement, etc.
    self._report = dict(template, rows=[
        dict(table_row, data={rev: [] for rev in revisions})
        for table_row in template['rows']])
    self._revisions = revisions
    self._max_revs = {}

  def FetchSync(self):
    return self.FetchAsync().get_result()

  @ndb.tasklet
  def FetchAsync(self):
    # Get data for each descriptor in each table row in parallel.
    futures = []
    for tri, table_row in enumerate(self._report['rows']):
      for test_suite in table_row['testSuites']:
        for bot in table_row['bots']:
          for case in table_row['testCases']:
            desc = descriptor.Descriptor(
                test_suite, table_row['measurement'], bot, case)
            futures.append(self._GetRow(tri, table_row['data'], desc))
          if not table_row['testCases']:
            desc = descriptor.Descriptor(
                test_suite, table_row['measurement'], bot)
            futures.append(self._GetRow(tri, table_row['data'], desc))
    yield futures
    self._MergeCells()
    raise ndb.Return(self._report)

  def _MergeCells(self):
    # _GetRow can't know whether a datum will be merged until all the data have
    # been fetched, so post-process.
    for tri, table_row in enumerate(self._report['rows']):
      # Ignore data from test cases that were removed.
      for rev, data in table_row['data'].iteritems():
        new_data = []
        for datum in data:
          mrk = (datum['descriptor'].test_suite, datum['descriptor'].bot, tri,
                 rev)
          if datum['revision'] == self._max_revs[mrk]:
            new_data.append(datum)
        table_row['data'][rev] = new_data

      # Ignore data from test cases that are not present for every rev.
      for rev, data in table_row['data'].iteritems():
        table_row['data'][rev] = [
            datum for datum in data
            if all(any(other_datum['descriptor'] == datum['descriptor']
                       for other_datum in other_data)
                   for other_data in table_row['data'].itervalues())]

      # Copy units from the first datum to the table_row.
      # Sort data first so this is deterministic.
      for rev in self._revisions:
        data = table_row['data'][rev] = sorted(
            table_row['data'][rev], key=lambda datum: datum['descriptor'])
        if data:
          table_row['units'] = data[0]['units']
          table_row['improvement_direction'] = data[0]['improvement_direction']
          break

      # Ignore data with wrong units.
      for rev, data in table_row['data'].iteritems():
        table_row['data'][rev] = [
            datum for datum in data
            if datum['units'] == table_row['units']]

      # Merge remaining data.
      for rev, data in table_row['data'].iteritems():
        statistics = RunningStatistics()
        for datum in data:
          statistics = statistics.Merge(datum['statistics'])
        revision = rev
        if data:
          revision = data[0]['revision']
        table_row['data'][rev] = {
            'statistics': statistics.AsDict(),
            'descriptors': [
                {
                    'testSuite': datum['descriptor'].test_suite,
                    'bot': datum['descriptor'].bot,
                    'testCase': datum['descriptor'].test_case,
                }
                for datum in data
            ],
            'revision': revision,
        }

  @ndb.tasklet
  def _GetRow(self, tri, table_row, desc):
    # First try to find the unsuffixed test.
    unsuffixed_tests = yield [utils.TestMetadataKey(test_path).get_async()
                              for test_path in (yield desc.ToTestPathsAsync())]
    unsuffixed_tests = [t for t in unsuffixed_tests if t]

    if len(unsuffixed_tests) > 1:
      logging.warn('Found too many unsuffixed tests: %r', [
          utils.TestPath(t.key) for t in unsuffixed_tests])
      raise ndb.Return()

    if unsuffixed_tests:
      test = unsuffixed_tests[0]
      test_path = utils.TestPath(test.key)
      yield [self._GetUnsuffixedCell(tri, table_row, desc, test, test_path, rev)
             for rev in self._revisions]
      raise ndb.Return()

    # Fall back to suffixed tests.
    yield [self._GetSuffixedCell(tri, table_row, desc, rev)
           for rev in self._revisions]
    raise ndb.Return()

  @ndb.tasklet
  def _GetUnsuffixedCell(self, tri, table_row, desc, test, test_path, rev):
    data_row = yield self._GetDataRow(test_path, rev)
    if data_row is None:
      # Fall back to suffixed tests.
      yield self._GetSuffixedCell(tri, table_row, desc, rev)
      raise ndb.Return()

    statistics = {
        stat: getattr(data_row, 'd_' + stat)
        for stat in descriptor.STATISTICS
        if hasattr(data_row, 'd_' + stat)
    }
    if 'avg' not in statistics:
      statistics['avg'] = data_row.value
    if 'std' not in statistics and data_row.error:
      statistics['std'] = data_row.error
    datum = dict(
        descriptor=desc,
        units=test.units,
        improvement_direction=test.improvement_direction,
        revision=data_row.revision,
        statistics=_MakeRunningStatistics(statistics))
    table_row[rev].append(datum)

    mrk = (desc.test_suite, desc.bot, tri, rev)
    self._max_revs[mrk] = max(
        self._max_revs.get(mrk, 0), data_row.revision)

  @ndb.tasklet
  def _GetSuffixedCell(self, tri, table_row, desc, rev):
    datum = {'descriptor': desc}
    statistics = yield [self._GetStatistic(datum, desc, rev, stat)
                        for stat in descriptor.STATISTICS]
    statistics = {
        descriptor.STATISTICS[i]: statistics[i]
        for i in xrange(len(statistics))
        if statistics[i] is not None}
    if 'avg' not in statistics:
      raise ndb.Return()

    table_row[rev].append(datum)
    datum['statistics'] = _MakeRunningStatistics(statistics)

    mrk = (desc.test_suite, desc.bot, tri, rev)
    self._max_revs[mrk] = max(
        self._max_revs.get(mrk, 0), datum['revision'])

  @ndb.tasklet
  def _GetStatistic(self, datum, desc, rev, stat):
    desc = desc.Clone()
    desc.statistic = stat
    test_paths = yield desc.ToTestPathsAsync()
    suffixed_tests = yield [utils.TestMetadataKey(test_path).get_async()
                            for test_path in test_paths]
    suffixed_tests = [t for t in suffixed_tests if t]
    if not suffixed_tests:
      raise ndb.Return(None)
    if len(suffixed_tests) > 1:
      logging.warn('Found too many suffixed tests: %r', test_paths)
      raise ValueError
    test = suffixed_tests[0]
    if stat == 'avg':
      datum['units'] = test.units
      datum['improvement_direction'] = test.improvement_direction
    test_path = utils.TestPath(test.key)
    data_row = yield self._GetDataRow(test_path, rev)
    if not data_row:
      raise ndb.Return(None)
    datum['revision'] = data_row.revision
    raise ndb.Return(data_row.value)

  @ndb.tasklet
  def _GetDataRow(self, test_path, rev):
    entities = yield [
        self._GetDataRowForKey(utils.TestMetadataKey(test_path), rev),
        self._GetDataRowForKey(utils.OldStyleTestKey(test_path), rev)]
    entities = [e for e in entities if e]
    if not entities:
      raise ndb.Return(None)
    if len(entities) > 1:
      logging.warn('Found too many Row entities: %r %r', rev, test_path)
      raise ndb.Return(None)
    raise ndb.Return(entities[0])

  @ndb.tasklet
  def _GetDataRowForKey(self, test_key, rev):
    query = graph_data.Row.query(graph_data.Row.parent_test == test_key)
    if rev != 'latest':
      query = query.filter(graph_data.Row.revision <= rev)
    query = query.order(-graph_data.Row.revision)
    data_row = yield query.get_async()
    raise ndb.Return(data_row)


def _MakeRunningStatistics(statistics):
  if statistics.get('avg') is None:
    return None
  count = statistics.get('count', 10)
  std = statistics.get('std', 0)
  return RunningStatistics.FromDict([
      count,
      statistics.get('max', statistics['avg']),
      0,  # meanlogs for geometricMean
      statistics['avg'],
      statistics.get('min', statistics['avg']),
      statistics.get('sum', statistics['avg'] * count),
      std * std * (count - 1)])
