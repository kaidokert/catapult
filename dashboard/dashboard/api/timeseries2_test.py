# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from dashboard.api import timeseries2
from dashboard.common import testing_common
from dashboard.models import anomaly
from dashboard.models import graph_data
from dashboard.models import histogram


class Timeseries2Test(testing_common.TestCase):

  def setUp(self):
    super(Timeseries2Test, self).setUp()

  def testMixOldStyleRowsWithNewStyleRows(self):
    response = self._Post(
        test_suite='suite', measurement='measure', bot='master:bot',
        test_case='case', statistic='avg', build_type='test',
        columns='revision,revisions,avg,std,alert,diagnostics,histogram')

  def testCollateAllColumns(self):
    for i in xrange(100):
      graph_data.Row(parent=parent, id=i, value=float(i)).put()
    response = self._Post(
        test_suite='suite', measurement='measure', bot='master:bot',
        test_case='case', statistic='avg', build_type='test',
        columns='revision,revisions,avg,std,alert,diagnostics,histogram')

  def testRange(self):
    response = self._Post(
        test_suite='suite', measurement='measure', bot='master:bot',
        test_case='case', statistic='avg', build_type='test',
        min_rev=10, max_rev=90,
        columns='revision,revisions,avg,std,alert,diagnostics,histogram')
