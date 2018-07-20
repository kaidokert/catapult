# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provides an endpoint for handling storing and retrieving page states."""

import hashlib
import json

from google.appengine.ext import ndb

from dashboard import list_tests
from dashboard.common import descriptor
from dashboard.common import request_handler
from dashboard.models import page_state


def UpgradeChart(chart):
  suites = set()
  measurements = set()
  bots = set()
  cases = set()
  for prefix, suffixes in chart:
    if suffixes == ['all']:
      paths = list_tests.GetTestsMatchingPattern(
          prefix + '/*', only_with_rows=True)
    else:
      paths = [prefix + '/' + suffix for suffix in suffixes]
    for path in paths:
      desc = descriptor.Descriptor.FromTestPathSync(path)
      suites.add(desc.test_suite)
      bots.add(desc.bot)
      measurements.add(desc.measurement)
      if desc.test_case:
        cases.add(desc.test_case)
  return {
      'parameters': {
          'testSuites': list(suites),
          'measurements': list(measurements),
          'bots': list(bots),
          'testCases': list(cases),
      },
  }


def Upgrade(statejson):
  try:
    state = json.loads(statejson)
  except ValueError:
    return statejson
  if not state.get('charts'):
    return statejson
  state = {
      'showingReportSection': False,
      'chartSections': [
          UpgradeChart(chart) for chart in state['charts']
      ],
  }
  statejson = json.dumps(state)
  return statejson


class ShortUriHandler(request_handler.RequestHandler):
  """Handles short URI."""

  def get(self):
    """Handles getting page states."""
    state_id = self.request.get('sid')

    if not state_id:
      self.ReportError('Missing required parameters.', status=400)
      return

    state = ndb.Key(page_state.PageState, state_id).get()

    if not state:
      self.ReportError('Invalid sid.', status=400)
      return

    state = state.value
    if self.request.get('v2'):
      state = Upgrade(state)
    self.response.out.write(state)

  def post(self):
    """Handles saving page states and getting state id."""

    state = self.request.get('page_state')

    if not state:
      self.ReportError('Missing required parameters.', status=400)
      return

    state_id = GetOrCreatePageState(state)

    self.response.out.write(json.dumps({'sid': state_id}))


def GetOrCreatePageState(state):
  state = state.encode('utf-8')
  state_id = GenerateHash(state)
  if not ndb.Key(page_state.PageState, state_id).get():
    page_state.PageState(id=state_id, value=state).put()
  return state_id


def GenerateHash(state_string):
  """Generates a hash for a state string."""
  return hashlib.sha256(state_string).hexdigest()
