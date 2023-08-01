# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Helpers for handling Buganizer migration.

Monorail is being deprecated and replaced by Buganizer in 2024. Migration
happens by projects. Chromeperf needs to support both Monorail and Buganizer
during the migration until the last project we supported is fully migrated.

Before the first migration happens, we will keep the consumers untouched
in the Monorail fashion. The requests and responses to and from Buganizer will
be reconciled to the Monorail format on perf_issue_service.
"""

import logging

# ============ mapping helpers start ============
# The mapping will be different from project to project.
def FindBuganizerComponents(monorail_project_name):
  """return a list of components in buganizer based on the monorail project

  The current implementation is ad hoc as the component mappings are not
  fully set up on buganizer yet.
  """
  if monorail_project_name == 'MigratedProject':
    return ['1325852']
  return []

def FindMonorailProject(buganizer_component_id):
  if buganizer_component_id == '1325852':
    return 'MigratedProject'
  return ''


def FindBuganizerHotlists(monorail_labels):
  hotlists = []
  for label in monorail_labels:
    hotlist = _FindBuganizerHotlist(label)
    if hotlist:
      hotlists.append(hotlist)
  logging.debug(
    '[PerfIssueService] labels (%s) -> hotlists (%s)',
    monorail_labels, hotlists)
  return hotlists


def _FindBuganizerHotlist(monorail_label):
  if monorail_label == 'chromeperf-test':
    return '5141966'
  elif monorail_label == 'chromeperf-test-2':
    return '5142065'
  return None


def _FindMonorailLabel(buganizer_hotlist):
  if buganizer_hotlist == '5141966':
    return 'chromeperf-test'
  elif buganizer_hotlist == '5142065':
    return 'chromeperf-test-2'
  return None


def _FindMonorailStatus(buganizer_status):
  if buganizer_status == 'NEW':
    return 'Untriaged'
  elif buganizer_status == 'ASSIGNED':
    return "Assigned"
  elif buganizer_status == 'ACCEPTED':
    return 'Started'
  elif buganizer_status == 'FIXED':
    return 'Fixed'
  elif buganizer_status == 'VERIFIED':
    return 'Verified'
  return 'Unconfirmed'

# ============ mapping helpers end ============

def GetBuganizerStatusUpdate(issue_update):
  _BUGANIZER_STATUS_MAP = {
    0: "STATUS_UNSPECIFIED",
    1: "NEW",
    2: "ASSIGNED",
    3: "ACCEPTED",
    4: "FIXED",
    5: "VERIFIED",
    6: "NOT_REPRODUCIBLE",
    7: "INTENDED_BEHAVIOR",
    8: "OBSOLETE",
    9: "INFEASIBLE",
    10: "DUPLICATE"
  }

  for field_update in issue_update.get('fieldUpdates', []):
    if field_update.get('field') == 'status':
      new_status = field_update.get('singleValueUpdate').get('newValue').get('value')

      # The current status returned from issueUpdate is integer, which is
      # different from the definition in the discovery doc.
      # I'm using a map to workaround it for now.
      status_update = {
        'status': _FindMonorailStatus(_BUGANIZER_STATUS_MAP[new_status])
      }
      return status_update
  return None


def ReconcileBuganizerIssue(buganizer_issue):
  '''Reconcile a Buganizer issue into the Monorail format

  During the Buganizer migration, we try to minimize the changes on the
  consumers of the issues. Thus, we will reconcile the results into the
  exising Monorail format before returning the results.
  '''
  monorail_issue = {}
  issue_state = buganizer_issue.get('issueState')

  monorail_issue['projectId'] = FindMonorailProject(issue_state['componentId'])
  monorail_issue['id'] = buganizer_issue['issueId']
  buganizer_status = issue_state['status']
  if buganizer_status in ('NEW', 'ASSIGNED', 'ACCEPTED'):
    monorail_issue['state'] = 'open'
  else:
    monorail_issue['state'] = 'closed'
  monorail_issue['status'] = _FindMonorailStatus(buganizer_status)
  monorail_author = {
    'name': issue_state['reporter']
  }
  monorail_issue['author'] = monorail_author
  monorail_issue['summary'] = issue_state['title']
  monorail_issue['owner'] = issue_state.get('assignee', None)

  hotlist_ids = buganizer_issue.get('hotlistIds', [])
  label_names = [_FindMonorailLabel(hotlist_id) for hotlist_id in hotlist_ids]
  monorail_issue['labels'] = [label for label in label_names if label]

  return monorail_issue
