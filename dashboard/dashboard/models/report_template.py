# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from google.appengine.ext import ndb

from dashboard.common import descriptor
from dashboard.common import timing
from dashboard.common import utils
from dashboard.models import graph_data
from dashboard.models import histogram
from dashboard.models import internal_only_model


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

  def __init__(self, template, revisions):
    # Clone the template so that we can set table_row[revision] and the client
    # still gets to see the statistics, row testSuites, measurement, etc.
    self._report = dict(template)
    self._report['rows'] = [
        dict(table_row) for table_row in self._report['rows']]
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
            futures.append(self._MergeRow(table_row, descriptor.Descriptor(
                test_suite, table_row['measurement'], bot, case)))
    yield futures
    raise ndb.Return(self._report)

  @ndb.tasklet
  def _MergeRow(self, table_row, desc):
    # First try to find the unsuffixed test.
    unsuffixed_tests = yield [utils.TestMetadataKey(test_path).get_async()
                              for test_path in (yield desc.ToTestPathsAsync())]
    unsuffixed_tests = [t for t in unsuffixed_tests if t]

    if not unsuffixed_tests:
      # Fall back to suffixed tests.
      yield [self._MergeSuffixedRow(table_row, desc, stat)
             for stat in self._report['statistics']]
      raise ndb.Return()

    if len(unsuffixed_tests) > 1:
      logging.warn('Found too many unsuffixed tests: %r', [
          utils.TestPath(t.key) for t in unsuffixed_tests])
      raise ndb.Return()

    # If there is 1 unsuffixed test, get the rows <= self._revisions.
    test_path = utils.TestPath(unsuffixed_tests[0].key)
    yield [self._MergeUnsuffixedCell(table_row, test_path, rev, desc)
           for rev in self._revisions]

  @ndb.tasklet
  def _MergeUnsuffixedCell(self, table_row, test_path, rev, desc):
    data_row = yield self._GetDataRow(test_path, rev)
    if data_row is None:
      # Fall back to suffixed tests.
      yield [self._MergeSuffixedRow(table_row, desc, stat)
             for stat in self._report['statistics']]
      raise ndb.Return()

    # |rev| may be 'latest' or slightly larger than |data_row.revision|
    rev = data_row.revision
    hist = yield self._GetHistogram(test_path, rev)
    if not hist:
      raise ndb.Return() # TODO merge data_row into table_row[rev]

    # TODO merge hist into table_row[rev]

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
    query = histogram.Histogram.query(
        histogram.Histogram.test == utils.TestMetadataKey(test_path),
        histogram.Histogram.revision == rev)
    hist = yield query.get_async()
    raise ndb.Return(hist)

  @ndb.tasklet
  def _MergeSuffixedRow(self, unused_table_row, desc, stat):
    desc = desc.Clone()
    desc.statistic = stat
    test_paths = yield desc.ToTestPathsAsync()
    suffixed_tests = yield [utils.TestMetadataKey(test_path).get_async()
                            for test_path in test_paths]
    suffixed_tests = [t for t in suffixed_tests if t]
    if not suffixed_tests:
      raise ndb.Return()
    if len(suffixed_tests) > 1:
      logging.warn('Found too many suffixed tests: %r', test_paths)
      raise ValueError
    yield [self._MergeSuffixedDataRows(),
           self._MergeSuffixedDataRows()]
    # Get the rows <= self._revisions.
    # Merge them into table_row[rev].
