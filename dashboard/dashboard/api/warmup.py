# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import random

from google.appengine.ext import ndb

from dashboard import add_histograms
from dashboard import update_test_suite_descriptors
from dashboard import update_test_suites
from dashboard.api import api_request_handler
from dashboard.common import datastore_hooks
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import graph_data
from dashboard.models import report_template
from tracing.tracing.value import histogram_set
from tracing.tracing.value import reserved_infos
from tracing.tracing.value.diagnostics import generic_set


CLEAR_KINDS = [
    anomaly.Anomaly,
    graph_data.Row,
    graph_data.TestMetadata,
    report_template.ReportTemplate,
]


def ClearData():
  assert utils.IsDevAppserver()
  for kind in CLEAR_KINDS:
    ndb.delete_multi(kind.query().fetch(keys_only=True))


def Noise(magnitude=1):
  return random.random() * magnitude


def CreateFakeData(index, rts, bot, suite, case=None):
  # Simulate a regression. The unit is biggerIsBetter, start high then drop down
  # after a few data points
  baseline = 5 if index < 50 else 0

  hs = histogram_set.HistogramSet()
  for name in range(10):
    hs.CreateHistogram('measurement' + name, 'unitless_biggerIsBetter',
                       [baseline + Noise() for _ in range(10)])

  hs.AddSharedDiagnosticToAllHistograms(
      reserved_infos.BOTS.name, generic_set.GenericSet([bot]))
  hs.AddSharedDiagnosticToAllHistograms(
      reserved_infos.REVISION_TIMESTAMPS.name, generic_set.GenericSet([rts]))
  hs.AddSharedDiagnosticToAllHistograms(
      reserved_infos.BENCHMARKS.name, generic_set.GenericSet([suite]))
  if case:
    hs.AddSharedDiagnosticToAllHistograms(
        reserved_infos.STORIES.name, generic_set.GenericSet([case]))

  return hs.AsDicts()


def AddFakeData(revs=500, suites=3, bots=3, cases=10):
  now = datetime.datetime.now()
  for suite in range(suites):
    suite = 'test_suite_' + suite
    for d in range(revs):
      rts = now - datetime.timedelta(days=(revs - 1 - d))
      for bot in range(bots):
        add_histograms.ProcessHistogramSet(CreateFakeData(
            d, rts, 'TestMaster:bot' + bot, suite))
        for case in range(cases):
          add_histograms.ProcessHistogramSet(CreateFakeData(
              d, rts, 'TestMaster:bot' + bot, suite,
              'case' + case))
    update_test_suite_descriptors._UpdateDescriptor(
        suite, datastore_hooks.EXTERNAL)


class WarmupHandler(api_request_handler.ApiRequestHandler):
  def _CheckUser(self):
    pass

  def get(self):
    if not utils.IsDevAppserver():
      return

    ClearData()
    AddFakeData()

    update_test_suites.UpdateTestSuites(datastore_hooks.EXTERNAL)
    report_template.PutTemplate(
        None, 'Chromium Performance Overview', ['test@example.com'], {
            'rows': [
                {
                    'testSuites': ['test_suite_' + i for i in range(1)],
                    'bots': ['TestMaster:bot' + i for i in range(1)],
                    'testCases': ['case' + i for i in range(1)],
                    'measurement': 'measurement' + name,
                }
                for name in range(4)
            ],
        })
    # XXX prepopulate reports
