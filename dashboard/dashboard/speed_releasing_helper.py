# Copyright 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Provides the speed releasing help functions."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from google.appengine.ext import ndb

from dashboard.common import datastore_hooks
from dashboard.common import graph_data
from dashboard.common import utils
from dashboard.modals import anomaly


CLANK_MILESTONES = {
    54: (1473196450, 1475824394),
    55: (1475841673, 1479536199),
    56: (1479546161, 1485025126),
    57: (1486119399, 1488528859),
    58: (1488538235, 1491977185),
    59: (1492542658, 1495792284),
    60: (1495802833, 1500610872),
    61: (1500628339, 1504160258),
    62: (1504294629, 1507887190),
    63: (1507887190, 1512141580),
    64: (1512154460, 1516341121),
    65: (1516353162, 1519951206),
    66: (1519963059, 1523653340),
    67: (1523629648, None),
}

CHROMIUM_MILESTONES = {
    54: (416640, 423768),
    55: (433391, 433400),
    56: (433400, 445288),
    57: (447949, 454466),
    58: (454523, 463842),
    59: (465221, 474839),
    60: (474952, 488392),
    61: (488576, 498621),
    62: (499187, 508578),
    63: (508578, 520719),
    64: (520917, 530282),
    65: (530373, 540240),
    66: (540302, 550534),
    67: (554148, None),
}

CURRENT_MILESTONE = max(CHROMIUM_MILESTONES.keys())


def GetDisplayRev(bots, tests, rev):
  """Creates a user friendly commit position to display.
  For V8 and ChromiumPerf masters, this will just be the passed in rev.
  """
  if bots and tests:
    test_path = bots[0] + '/' + tests[0]
    test_key = utils.TestKey(test_path)
    row_key = utils.GetRowKey(test_key, rev)
    row = row_key.get()
    if row and hasattr(row, 'r_commit_pos'):  # Rule out masters like V8
      if rev != row.r_commit_pos:  # Rule out ChromiumPerf
        if hasattr(row, 'a_default_rev') and hasattr(row, row.a_default_rev):
          return row.r_commit_pos + '-' + getattr(row, row.a_default_rev)[:3]
  return rev


def UpdateNewestRevInMilestoneDict(bots, tests, milestone_dict):
  """Updates the most recent rev in the milestone dict.

  The global milestone dicts are declared with 'None' for the end of the
  current milestone range. If we might be using the last milestone, update
  the end of the current milestone range to be the most recent revision.
  """
  if bots and tests:
    test_path = bots[0] + '/' + tests[0]
    test_key = utils.TestKey(test_path)
    # Need to allow set this request as privileged in order to bypass datastore
    # hooks. This is okay here because table_config is internal_only protected
    # and will ensure that only the correct users can see internal_only data.
    datastore_hooks.SetSinglePrivilegedRequest()
    query = graph_data.Row.query()
    query = query.filter(
        graph_data.Row.parent_test == utils.OldStyleTestKey(test_key))
    query = query.order(-graph_data.Row.revision)  # pylint: disable=invalid-unary-operand-type
    row = query.get()
    if row:
      milestone_dict[CURRENT_MILESTONE] = (milestone_dict[CURRENT_MILESTONE][0],
                                           row.revision)
    else:
      milestone_dict[CURRENT_MILESTONE] = (milestone_dict[CURRENT_MILESTONE][0],
                                           milestone_dict[CURRENT_MILESTONE][0])


def GetEndOfMilestone(rev, milestone_dict):
  """Finds the end of the milestone that 'rev' is in.

  Check that 'rev' is between [beginning, end) of the tuple. In case an end
  'rev' is passed in, return corresponding beginning rev. But since revs can
  double as end and beginning, favor returning corresponding end rev if 'rev'
  is a beginning rev.
  """
  beginning_rev = 0
  for _, value_tuple in milestone_dict.items():
    if value_tuple[0] <= int(rev) < value_tuple[1]:  # 'rev' is a beginning rev.
      return value_tuple[1]  # Favor by returning here.
    if value_tuple[1] == int(rev):  # 'rev' is an end rev.
      beginning_rev = value_tuple[0]
  if beginning_rev:
    return beginning_rev
  return milestone_dict[CURRENT_MILESTONE][1]


def GetEndRevOrCurrentMilestoneRevs(rev_a, rev_b, milestone_dict):
  """If one/both of the revisions are None, change accordingly.

  If both are None, return most recent milestone, present.
  If one is None, return the other, end of that milestone.
  """
  if not rev_a and not rev_b:
    return milestone_dict[CURRENT_MILESTONE]
  return (rev_a or rev_b), GetEndOfMilestone((rev_a or rev_b), milestone_dict)


def GetUpdatedMilestoneDict(master_bot_pairs, tests):
  """Gets the milestone_dict with the newest rev.

  Checks to see which milestone_dict to use (Clank/Chromium), and updates
  the 'None' to be the newest revision for one of the specified tests.
  """
  masters = {m.split('/')[0] for m in master_bot_pairs}
  if 'ClankInternal' in masters:
    milestone_dict = CLANK_MILESTONES.copy()
  else:
    milestone_dict = CHROMIUM_MILESTONES.copy()
  # If we might access the end of the milestone_dict, update it to
  # be the newest revision instead of 'None'.
  UpdateNewestRevInMilestoneDict(master_bot_pairs, tests, milestone_dict)
  return milestone_dict


def FetchAnomalies(table_entity, rev_a, rev_b):
  """Finds anomalies that have the given benchmark/master, in a given range."""
  if table_entity.bots and table_entity.tests:
    master_list = []
    benchmark_list = []
    for bot in table_entity.bots:
      if bot.parent().string_id() not in master_list:
        master_list.append(bot.parent().string_id())
    for test in table_entity.tests:
      if test.split('/')[0] not in benchmark_list:
        benchmark_list.append(test.split('/')[0])
  else:
    return []

  anomalies_futures = []
  for benchmark in benchmark_list:
    for master in master_list:
      anomalies_futures.append(
          anomaly.Anomaly.QueryAsync(
              min_end_revision=rev_a,
              max_end_revision=rev_b,
              test_suite_name=benchmark,
              master_name=master))

  ndb.Future.wait_all(anomalies_futures)
  all_anomalies = [future.get_result()[0] for future in anomalies_futures]
  # Flatten list of lists.
  all_anomalies = [a for future_list in all_anomalies for a in future_list]

  anomalies = []
  for anomaly_entity in all_anomalies:
    for test in table_entity.tests:
      if test in utils.TestPath(anomaly_entity.test):
        anomalies.append(anomaly_entity)
        break
  anomalies = [a for a in anomalies if not a.is_improvement]

  return anomalies


def GetMilestoneForRevs(rev_a, rev_b, milestone_dict):
  """Determines which milestone each revision is part of. Returns a tuple."""
  rev_a_milestone = CURRENT_MILESTONE
  rev_b_milestone = CURRENT_MILESTONE

  for key, milestone in milestone_dict.items():
    if milestone[0] <= rev_a < milestone[1]:
      rev_a_milestone = key
    if milestone[0] < rev_b <= milestone[1]:
      rev_b_milestone = key
  return rev_a_milestone, rev_b_milestone


def GetNavigationMilestones(rev_a_milestone, rev_b_milestone, milestone_dict):
  """Finds the next/previous milestones for navigation, if available.

  Most often, the milestones will be the same (e.g. the report for M57 will
  have both rev_a_milestone and rev_b_milestone as 57; the navigation in this
  case is 56 for back and 58 for forward). If the milestone is at either the
  lower or upper bounds of the milestones that we support, return None (so
  users can't navigate to an invalid milestone). In the case that the
  revisions passed in cover multiple milestones (e.g. a report from
  M55 -> M57), the correct navigation is 54 (back) and 57 (forward).
  """
  min_milestone = min(milestone_dict)

  if rev_a_milestone == min_milestone:
    navigation_milestone_a = None
  else:
    navigation_milestone_a = rev_a_milestone - 1

  if rev_b_milestone == CURRENT_MILESTONE:
    navigation_milestone_b = None
  elif rev_a_milestone != rev_b_milestone:  # In the multiple milestone case.
    navigation_milestone_b = rev_b_milestone
  else:
    navigation_milestone_b = rev_b_milestone + 1

  return navigation_milestone_a, navigation_milestone_b
