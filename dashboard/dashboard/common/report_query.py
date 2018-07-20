# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from google.appengine.ext import ndb

from dashboard.common import descriptor


def TableRowDescriptors(table_row):
  for test_suite in table_row['testSuites']:
    for bot in table_row['bots']:
      for case in table_row['testCases']:
        yield descriptor.Descriptor(
            test_suite, table_row['measurement'], bot, case)
      if not table_row['testCases']:
        yield descriptor.Descriptor(test_suite, table_row['measurement'], bot)


class ReportQuery(object):

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
    raise ndb.Return(self._report)
