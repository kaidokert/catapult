# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from dashboard.api import api_request_handler
from dashboard.common import descriptor


class ReportHandler(api_request_handler.ApiRequestHandler):

  def _AllowAnonymous(self):
    return True

  def AuthorizedPost(self):
    if self.request.get('template'):
      return self._PutTemplate()
    return self._GetReport()

  def _PutTemplate(self):
    template = self.request.get('template')
    name = self.request.get('name')
    owners = self.request.get('owners')

  def _GetReport(self):
    revisions = self.request.get('revisions', None)
    if revisions is None:
      raise api_request_handler.BadRequestError
    template_id = self.request.get('id')
    template = ndb.Key('ReportTemplate', template_id).get()
    if template is None:
      raise api_request_handler.NotFoundError
    report = dict(template.template)
    query = ReportQuery(
        template.template['rows'], template.template['statistics'], revisions)
    report['rows'] = query.FetchSync()
    return {
        'id': template.key.id(),
        'name': template.name,
        'internal': template.internal_only,
        'report': report,
    }


class ReportQuery(object):

  def __init__(self, rows, statistics, revisions):
    self._rows = rows
    self._statistics = statistics
    self._revisions = revisions

  def FetchSync(self):
    return self.FetchAsync().get_result()

  @ndb.tasklet
  def FetchAsync(self):
    rows = yield [self._FetchRow(row) for row in self._rows]
    raise ndb.Return(rows)

  @ndb.tasklet
  def _FetchRow(self, row):
    test_keys = []
    for test_suite in row['testSuites']:
      for bot in row['bots']:
        for case in row['testCases']:
          desc = descriptor.Descriptor(
              test_suite, row['measurement'], bot, case))
          for stat in [None] + self._statistics:
            desc.statistic = stat
            for test_path in (yield desc.ToTestPathsAsync()):
              test_keys.append(utils.TestMetadataKey(test_path))
              test_keys.append(utils.OldStyleTestKey(test_path))
    tests = yield [key.get_async() for key in test_keys]
    tests = [test for test in tests if test]
    # TODO fetch TestMetadata in parallel
    cells = yield [self._FetchCell(tests, rev) for rev in self._revisions]
    cells = dict(zip(self._revisions, cells))
    cells['label'] = row['label']
    raise ndb.Return(cells)

  @ndb.tasklet
  def _FetchCell(self, tests, rev):
    cell = {}
    values = yield [self._FetchValue(
    raise ndb.Return(cell)
