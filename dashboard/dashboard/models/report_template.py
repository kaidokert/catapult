# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from google.appengine.ext import ndb

from dashboard.common import descriptor
from dashboard.common import timing
from dashboard.common import utils
from dashboard.models import graph_data
from dashboard.models import histogram as histogram_model
from dashboard.models import internal_only_model
from tracing.value import histogram as histogram_module


HistogramModel = histogram_model.Histogram
Histogram = histogram_module.Histogram
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


# @Static(
#     internal_only=False,
#     id='9925dc1c-894e-464a-a235-6315be6224d6',
#     name='Test:Beeeep',
#     modified=datetime.datetime(2018, 7, 13, 11, 8, 37, 39900))
# def Beeper(revisions):
#   return 'beeeep'
#   # Alternatively (see ReportQuery for the format of |template|)
#   return ReportQuery(template, revisions)
#   # Alternatively, return a subclass of ReportQuery


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
  if template_id is None:
    entity = ReportTemplate(owners=owners)
  else:
    for handler in STATIC_TEMPLATES:
      if handler.template.id == template_id:
        raise ValueError

    entity = ndb.Key('ReportTemplate', template_id).get()
    if not entity:
      raise ValueError

  email = utils.GetEmail()
  if email is None or email not in entity.owners:
    raise ValueError

  entity.name = name
  entity.owners = owners
  entity.template = template
  entity.put()


def GetReport(template_id, revisions):
  with timing.WallTimeLogger('GetReport'), timing.CpuTimeLogger('GetReport'):
    template = ndb.Key('ReportTemplate', template_id).get()
    result = {}
    if template:
      result['report'] = ReportQuery(template.template, revisions).FetchSync()
    else:
      for handler in STATIC_TEMPLATES:
        if handler.template.id == template_id:
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
        label, testSuites, measurement, bots, testCases,
        data: {
          [revision]: {
            statistics: {[stat]: {units, value}},
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

  def FetchSync(self):
    return self.FetchAsync().get_result()

  @ndb.tasklet
  def FetchAsync(self):
    futures = []
    for table_row in self._report['rows']:
      for test_suite in table_row['testSuites']:
        for bot in table_row['bots']:
          for case in table_row['testCases']:
            desc = descriptor.Descriptor(
                test_suite, table_row['measurement'], bot, case)
            futures.append(self._GetRow(table_row['data'], desc))
    yield futures
    # At some point maybe _GetRow can merge Histograms in
    # table_row['data'][rev], but for now it collects lists of dicts like
    # {descriptor,units,improvement_direction,revision,statistics}
    # There should be one such dict per descriptor in each
    # table_row['data'][rev].
    for table_row in self._report['rows']:
      for rev, data in table_row['data'].iteritems():
        table_row['data'][rev] = self._MergeCell(data)
    raise ndb.Return(self._report)

  def _MergeCell(self, data):
    descriptors = []
    statistics = RunningStatistics()
    if not data:
      return dict(statistics=statistics, descriptors=descriptors)

    max_rev_by_suitebot = {}
    for datum in data:
      suitebot = datum['descriptor'].test_suite + '/' + datum['descriptor'].bot
      max_rev_by_suitebot[suitebot] = max(
          datum['revision'], max_rev_by_suitebot.get(suitebot, 0))
    for datum in data:
      suitebot = datum['descriptor'].test_suite + '/' + datum['descriptor'].bot
      if datum['revision'] != max_rev_by_suitebot[suitebot]:
        # Ignore data from test cases that were disabled.
        continue
      descriptors.append(dict(
          suite=datum['descriptor'].test_suite,
          bot=datum['descriptor'].bot,
          case=datum['descriptor'].test_case,
          revision=datum['revision']))
      statistics = statistics.Merge(datum['statistics'])
    return dict(statistics=statistics, descriptors=descriptors)

  @ndb.tasklet
  def _GetRow(self, table_row, desc):
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
      yield [self._GetUnsuffixedCell(table_row, desc, test, test_path, rev)
             for rev in self._revisions]
      raise ndb.Return()

    # Fall back to suffixed tests.
    yield [self._GetSuffixedCell(table_row, desc, rev)
           for rev in self._revisions]
    raise ndb.Return()

  @ndb.tasklet
  def _GetUnsuffixedCell(self, table_row, desc, test, test_path, rev):
    data_row = yield self._GetDataRow(test_path, rev)
    if data_row is None:
      # Fall back to suffixed tests.
      yield self._GetSuffixedCell(table_row, desc, rev)
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
    table_row[rev].append(dict(
        descriptor=desc,
        units=test.units,
        improvement_direction=test.improvement_direction,
        revision=data_row.revision,
        statistics=_MakeRunningStatistics(statistics)))

  @ndb.tasklet
  def _GetSuffixedCell(self, table_row, desc, rev):
    datum = dict(descriptor=desc)
    statistics = yield [self._GetStatistic(datum, desc, rev, stat)
                        for stat in descriptor.STATISTICS]
    statistics = dict(zip(descriptor.STATISTICS, statistics))
    if statistics['avg'] is None:
      raise ndb.Return()
    table_row[rev].append(datum)
    datum['statistics'] = _MakeRunningStatistics(statistics)

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

  @ndb.tasklet
  def _GetHistogram(self, test_path, rev):
    query = HistogramModel.query(
        HistogramModel.test == utils.TestMetadataKey(test_path),
        HistogramModel.revision == rev)
    hist = yield query.get_async()
    raise ndb.Return(hist)


def _MakeRunningStatistics(statistics):
  if statistics.get('avg') is None:
    return None
  std = statistics.get('std', 0)
  return RunningStatistics.FromDict([
      statistics.get('count', 1),
      statistics.get('max', statistics['avg']),
      0,  # meanlogs for geometricMean
      statistics['avg'],
      statistics.get('min', statistics['avg']),
      statistics.get('sum', statistics['avg']),
      std * std])
