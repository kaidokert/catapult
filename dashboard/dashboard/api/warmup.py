# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import random

from dashboard import add_histograms
from dashboard import update_test_suite_descriptors
from dashboard import update_test_suites
from dashboard.api import api_request_handler
from dashboard.common import datastore_hooks
from dashboard.common import utils
from tracing.tracing.value import histogram_set


def CreateFakeData(unused_rts, unused_bot, unused_suite, unused_case=None):
  hs = histogram_set.HistogramSet()
  # XXX create fake data
  for name in range(10):
    hs.CreateHistogram('measurement' + name, 'unitless_biggerIsBetter',
                       [random.random() for _ in range(10)])
  hs.AddSharedDiagnosticToAllHistograms('XXX', None)
  return hs.AsDicts()


def AddFakeData():
  for d in range(100):
    rts = datetime.datetime.now() - datetime.timedelta(days=(99-d))
    for suite in range(3):
      for bot in range(3):
        add_histograms.ProcessHistogramSet(CreateFakeData(
            rts, 'TestMaster:bot' + bot, 'test_suite_' + suite))
        for case in range(10):
          add_histograms.ProcessHistogramSet(CreateFakeData(
              rts, 'TestMaster:bot' + bot, 'test_suite_' + suite,
              'case' + case))


class WarmupHandler(api_request_handler.ApiRequestHandler):
  def _CheckUser(self):
    pass

  def get(self):
    if not utils.IsDevAppserver():
      return

    # XXX clear graph_data, alerts

    AddFakeData()

    update_test_suites.UpdateTestSuites(datastore_hooks.EXTERNAL)
    update_test_suite_descriptors._UpdateDescriptor(
        'suite', datastore_hooks.EXTERNAL)
    # XXX create alerts
    # XXX create report templates
