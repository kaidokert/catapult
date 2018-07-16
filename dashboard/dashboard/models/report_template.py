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
    # _GetRow can't know whether a datum will be merged until all the data have
    # been fetched, so post-process.
    for tri, table_row in enumerate(self._report['rows']):
      for rev, data in table_row['data'].iteritems():
        data = [datum for datum in data if self._MergeDatum(tri, rev, datum)]
        table_row['data'][rev] = data
      for rev, data in table_row['data'].iteritems():
        table_row['data'][rev] = self._MergeCell(data)
      # TODO table_row['units'], improvement_direction
    raise ndb.Return(self._report)

  def _MergeCell(self, data):
    descriptors = []
    statistics = RunningStatistics()
    for datum in data:
      descriptors.append(dict(
          suite=datum['descriptor'].test_suite,
          bot=datum['descriptor'].bot,
          case=datum['descriptor'].test_case,
          revision=datum['revision']))
      statistics = statistics.Merge(datum['statistics'])
    return {'statistics': statistics.AsDict(), 'descriptors': descriptors}

  def _MergeDatum(self, tri, rev, datum):
    mrk = (datum['descriptor'].test_suite, datum['descriptor'].bot, tri, rev)
    #file('occam','a').write('%r %r\n'%(datum, self._max_revs[mrk]))
    if datum['revision'] != self._max_revs[mrk]:
      # Ignore data from test cases that were disabled.
      return False

    # Ignore data from test cases that are not present for every rev in the row.
    for data in self._report['rows'][tri]['data'].itervalues():
      #file('occam','a').write('_MergeDatum ' + repr(data)+'\n')
      # Return False if |datum['descriptor']| is not in |data|.
      if not any(other_datum['descriptor'] == datum['descriptor']
                 for other_datum in data):
        return False

    # TODO ignore data with wrong units

    return True

  @ndb.tasklet
  def _GetRow(self, tri, table_row, desc):
    # First try to find the unsuffixed test.
    unsuffixed_tests = yield [utils.TestMetadataKey(test_path).get_async()
                              for test_path in (yield desc.ToTestPathsAsync())]
    unsuffixed_tests = [t for t in unsuffixed_tests if t]
    #file('occam','a').write('_GetRow %r\n' % [utils.TestPath(t.key) for t in unsuffixed_tests])

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
    #file('occam','a').write('_GetUnsuffixedCell %r\n' % data_row.to_dict() if data_row else data_row)
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
    #file('occam','a').write('xyz %r %r\n' % (statistics, data_row.error))
    if 'std' not in statistics and data_row.error:
      statistics['std'] = data_row.error
    #file('occam','a').write('%r\n' % statistics)
    datum = dict(
        descriptor=desc,
        units=test.units,
        improvement_direction=test.improvement_direction,
        revision=data_row.revision,
        statistics=_MakeRunningStatistics(statistics))
    table_row[rev].append(datum)
    #file('occam','a').write('%r %r\n' % (datum, datum['statistics'].stddev))

    mrk = (desc.test_suite, desc.bot, tri, rev)
    self._max_revs[mrk] = max(
        self._max_revs.get(mrk, 0), data_row.revision)
    #file('occam','a').write('%r %r\n' % (mrk, self._max_revs[mrk]))

  @ndb.tasklet
  def _GetSuffixedCell(self, tri, table_row, desc, rev):
    datum = {'descriptor': desc}
    statistics = yield [self._GetStatistic(datum, desc, rev, stat)
                        for stat in descriptor.STATISTICS]
    statistics = dict(zip(descriptor.STATISTICS, statistics))
    if statistics['avg'] is None:
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
    #file('occam','a').write('_GetDataRow %r %r\n' % (test_path, entities))
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
    #file('occam','a').write('_GetDataRowForKey %r %r %r\n' % (test_key, rev, data_row))
    raise ndb.Return(data_row)


def _MakeRunningStatistics(statistics):
  if statistics.get('avg') is None:
    return None
  count = statistics.get('count', 10)
  std = statistics.get('std', 0)
  if 'count' in statistics:
    count = statistics['count']
  else:
    # If the count is 1, then RunningStatistics forces stddev = 0.
    # However, faking the count requires fudging the variance.
    count = 10
    std *= 3
  return RunningStatistics.FromDict([
      count,
      statistics.get('max', statistics['avg']),
      0,  # meanlogs for geometricMean
      statistics['avg'],
      statistics.get('min', statistics['avg']),
      statistics.get('sum', statistics['avg'] * count),
      std * std])
