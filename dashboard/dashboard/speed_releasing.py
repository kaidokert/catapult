# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Provides the speed releasing table."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import logging
import six
import json

from google.appengine.ext import ndb

from dashboard import alerts
from dashboard import speed_releasing_helper
from dashboard.common import request_handler
from dashboard.models import table_config

# These represent the revision ranges per milestone. For Clank, this is a
# point id, for Chromium this is a Chromium commit position.

"""Request handler for requests for speed releasing page."""
from flask import make_response, request


def SpeedReleasingGet():
  """Renders the UI for the speed releasing page."""
  return request_handler.RequestHandlerRenderStaticHtml('speed_releasing.html')


def SpeedReleasingPost(tablename):
  """Returns dynamic data for /speed_releasing.

  Args:
    args: May contain the table_name for the requested Speed Releasing
          report. If args is empty, user is requesting the Speed Releasing
          landing page.
  Requested parameters:
    anomalies: A boolean that is set if the POST request is for the Release
               Notes alerts-table. Note, the table_name must also be passed
               in (via args) to retrieve the correct set of data.
  Outputs:
    JSON for the /speed_releasing page XHR request.
  """
  logging.debug('crbug/1298177 - /api/speed_releasing/.* handler triggered')
  anomalies = request.values.get('anomalies')
  if tablename and not anomalies:
    _OutputTableJSON(tablename)
  elif tablename:
    _OutputAnomaliesJSON(tablename)
  else:
    _OutputHomePageJSON()


def _OutputTableJSON(table_name):
  """Obtains the JSON values that comprise the table.

  Args:
    table_name: The name of the requested report.
  """
  table_entity = ndb.Key('TableConfig', table_name).get()
  if not table_entity:
    return make_response(json.dumps({'error': 'Invalid table name.'}))

  rev_a = request.values.get('revA')
  rev_b = request.values.get('revB')
  milestone_param = request.values.get('m')

  if milestone_param:
    milestone_param = int(milestone_param)
    if milestone_param not in speed_releasing_helper.CHROMIUM_MILESTONES:
      return make_response(json.dumps({'error': 'No data for that milestone.'}))

  master_bot_pairs = speed_releasing_helper.GetMasterBotPairs(table_entity.bots)
  rev_a, rev_b, milestone_dict = speed_releasing_helper.GetRevisionsFromParams(
      rev_a, rev_b, milestone_param, table_entity, master_bot_pairs)

  revisions = [rev_b, rev_a]  # In reverse intentionally. This is to support
  # the format of the Chrome Health Dashboard which compares 'Current' to
  # 'Reference', in that order. The ordering here is for display only.
  display_a = speed_releasing_helper.GetDisplayRev(
      master_bot_pairs, table_entity.tests, rev_a)
  display_b = speed_releasing_helper.GetDisplayRev(
      master_bot_pairs, table_entity.tests, rev_b)

  display_milestone_a, display_milestone_b = \
    speed_releasing_helper.GetMilestoneForRevs(rev_a, rev_b, milestone_dict)
  navigation_milestone_a, navigation_milestone_b = \
    speed_releasing_helper.GetNavigationMilestones(
        display_milestone_a, display_milestone_b, milestone_dict)

  values = {}
  request_handler.RequestHandlerGetDynamicVariables(values)
  return make_response(
      json.dumps({
          'xsrf_token':
            values['xsrf_token'],
          'table_bots':
            master_bot_pairs,
          'table_tests':
            table_entity.tests,
          'table_layout':
            json.loads(table_entity.table_layout),
          'name':
            table_entity.key.string_id(),
          'values':
            speed_releasing_helper.GetRowValues(
                revisions, master_bot_pairs, table_entity.tests),
          'units':
            speed_releasing_helper.GetTestToUnitsMap(
                master_bot_pairs, table_entity.tests),
          'revisions':
            revisions,
          'categories':
            speed_releasing_helper.GetCategoryCounts(
                json.loads(table_entity.table_layout)),
          'urls':
            speed_releasing_helper.GetDashboardURLMap(
                master_bot_pairs, table_entity.tests, rev_a, rev_b),
          'display_revisions': [display_b,
                                display_a],  # Similar to revisions.
          'display_milestones': [display_milestone_a, display_milestone_b],
          'navigation_milestones': [
              navigation_milestone_a, navigation_milestone_b
          ]
      }))


def _OutputHomePageJSON():
  """Returns a list of reports a user has permission to see."""
  all_entities = table_config.TableConfig.query().fetch()
  list_of_entities = []
  for entity in all_entities:
    list_of_entities.append(entity.key.string_id())
  return make_response(
      json.dumps({
          'show_list': True,
          'list': list_of_entities
      }))


def _OutputAnomaliesJSON(table_name):
  """Obtains the entire alert list specified.

  Args:
    table_name: The name of the requested report.
  """
  table_entity = ndb.Key('TableConfig', table_name).get()
  if not table_entity:
    return make_response(json.dumps({'error': 'Invalid table name.'}))

  rev_a = request.values.get('revA')
  rev_b = request.values.get('revB')
  milestone_param = request.values.get('m')

  if milestone_param:
    milestone_param = int(milestone_param)
    if milestone_param not in speed_releasing_helper.CHROMIUM_MILESTONES:
      return make_response(json.dumps({'error': 'No data for that milestone.'}))

  master_bot_pairs = speed_releasing_helper.GetMasterBotPairs(table_entity.bots)
  rev_a, rev_b, _ = speed_releasing_helper.GetRevisionsFromParams(
      rev_a, rev_b, milestone_param, table_entity, master_bot_pairs)
  revisions = [rev_b, rev_a]

  anomalies = speed_releasing_helper.FetchAnomalies(table_entity, rev_a, rev_b)
  anomaly_dicts = alerts.AnomalyDicts(anomalies)

  values = {}
  request_handler.RequestHandlerGetDynamicVariables(values)
  return make_response(
      json.dumps({
          'xsrf_token': values['xsrf_token'],
          'revisions': revisions,
          'anomalies': anomaly_dicts
      }))


if six.PY2:
  class SpeedReleasingHandler(request_handler.RequestHandler):
    """Request handler for requests for speed releasing page."""

    def get(self, *args):  # pylint: disable=unused-argument
      """Renders the UI for the speed releasing page."""
      self.RenderStaticHtml('speed_releasing.html')

    def post(self, *args):
      """Returns dynamic data for /speed_releasing.

      Args:
        args: May contain the table_name for the requested Speed Releasing
              report. If args is empty, user is requesting the Speed Releasing
              landing page.
      Requested parameters:
        anomalies: A boolean that is set if the POST request is for the Release
                   Notes alerts-table. Note, the table_name must also be passed
                   in (via args) to retrieve the correct set of data.
      Outputs:
        JSON for the /speed_releasing page XHR request.
      """
      logging.debug(
          'crbug/1298177 - /api/speed_releasing/.* project handler triggered')
      anomalies = self.request.get('anomalies')
      if args[0] and not anomalies:
        self._OutputTableJSON(args[0])
      elif args[0]:
        self._OutputAnomaliesJSON(args[0])
      else:
        self._OutputHomePageJSON()


    def _OutputTableJSON(self, table_name):
      """Obtains the JSON values that comprise the table.

      Args:
        table_name: The name of the requested report.
      """
      table_entity = ndb.Key('TableConfig', table_name).get()
      if not table_entity:
        self.response.out.write(json.dumps({'error': 'Invalid table name.'}))
        return

      rev_a = self.request.get('revA')
      rev_b = self.request.get('revB')
      milestone_param = self.request.get('m')

      if milestone_param:
        milestone_param = int(milestone_param)
        if milestone_param not in speed_releasing_helper.CHROMIUM_MILESTONES:
          self.response.out.write(
              json.dumps({'error': 'No data for that milestone.'}))
          return

      master_bot_pairs = speed_releasing_helper.GetMasterBotPairs(
          table_entity.bots)
      rev_a, rev_b, milestone_dict = \
        speed_releasing_helper.GetRevisionsFromParams(
          rev_a, rev_b, milestone_param, table_entity, master_bot_pairs)

      revisions = [rev_b, rev_a]  # In reverse intentionally. This is to support
      # the format of the Chrome Health Dashboard which compares 'Current' to
      # 'Reference', in that order. The ordering here is for display only.
      display_a = speed_releasing_helper.GetDisplayRev(
          master_bot_pairs, table_entity.tests, rev_a)
      display_b = speed_releasing_helper.GetDisplayRev(
          master_bot_pairs, table_entity.tests, rev_b)

      display_milestone_a, display_milestone_b = \
        speed_releasing_helper.GetMilestoneForRevs(
          rev_a, rev_b, milestone_dict)
      navigation_milestone_a, navigation_milestone_b = \
        speed_releasing_helper.GetNavigationMilestones(
          display_milestone_a, display_milestone_b, milestone_dict)

      values = {}
      self.GetDynamicVariables(values)
      self.response.out.write(
          json.dumps({
              'xsrf_token':
                values['xsrf_token'],
              'table_bots':
                master_bot_pairs,
              'table_tests':
                table_entity.tests,
              'table_layout':
                json.loads(table_entity.table_layout),
              'name':
                table_entity.key.string_id(),
              'values':
                speed_releasing_helper.GetRowValues(
                    revisions, master_bot_pairs, table_entity.tests),
              'units':
                speed_releasing_helper.GetTestToUnitsMap(
                    master_bot_pairs, table_entity.tests),
              'revisions':
                revisions,
              'categories':
                speed_releasing_helper.GetCategoryCounts(
                    json.loads(table_entity.table_layout)),
              'urls':
                speed_releasing_helper.GetDashboardURLMap(
                    master_bot_pairs, table_entity.tests, rev_a, rev_b),
              'display_revisions': [display_b,
                                    display_a],  # Similar to revisions.
              'display_milestones': [display_milestone_a, display_milestone_b],
              'navigation_milestones': [
                  navigation_milestone_a, navigation_milestone_b
              ]
          }))

    def _OutputHomePageJSON(self):
      """Returns a list of reports a user has permission to see."""
      all_entities = table_config.TableConfig.query().fetch()
      list_of_entities = []
      for entity in all_entities:
        list_of_entities.append(entity.key.string_id())
      self.response.out.write(
          json.dumps({
              'show_list': True,
              'list': list_of_entities
          }))

    def _OutputAnomaliesJSON(self, table_name):
      """Obtains the entire alert list specified.

      Args:
        table_name: The name of the requested report.
      """
      table_entity = ndb.Key('TableConfig', table_name).get()
      if not table_entity:
        self.response.out.write(json.dumps({'error': 'Invalid table name.'}))
        return
      rev_a = self.request.get('revA')
      rev_b = self.request.get('revB')
      milestone_param = self.request.get('m')

      if milestone_param:
        milestone_param = int(milestone_param)
        if milestone_param not in speed_releasing_helper.CHROMIUM_MILESTONES:
          self.response.out.write(
              json.dumps({'error': 'No data for that milestone.'}))
          return

      master_bot_pairs = speed_releasing_helper.GetMasterBotPairs(
          table_entity.bots)
      rev_a, rev_b, _ = speed_releasing_helper.GetRevisionsFromParams(
          rev_a, rev_b, milestone_param, table_entity, master_bot_pairs)
      revisions = [rev_b, rev_a]

      anomalies = speed_releasing_helper.FetchAnomalies(
          table_entity, rev_a, rev_b)
      anomaly_dicts = alerts.AnomalyDicts(anomalies)

      values = {}
      self.GetDynamicVariables(values)
      self.response.out.write(
          json.dumps({
              'xsrf_token': values['xsrf_token'],
              'revisions': revisions,
              'anomalies': anomaly_dicts
          }))
