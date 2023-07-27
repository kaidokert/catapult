# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from application.clients import datastore_client
from application.clients import sheriff_config_client


class NoEntityFoundException(Exception):
  pass


class SheriffConfigRequestException(Exception):
  pass

class AlertGroup:
  @classmethod
  def FindDuplicates(cls, group_id):
    client = datastore_client.DataStoreClient()

    filters = [('canonical_group', '=', client.AlertGroupKey(group_id))]
    duplicates = list(client.QueryAlertGroup(extra_filters=filters))

    return [client.GetEntityKey(g, key_type='name') for g in duplicates]


  @classmethod
  def FindCanonicalGroupByIssue(cls, current_group_key, issue_id, project_name):
    client = datastore_client.DataStoreClient()

    filters = [
      ('bug.bug_id', '=', issue_id),
      ('bug.project', '=', project_name)
    ]

    query_result = list(client.QueryAlertGroup(extra_filters=filters, limit=1))

    if not query_result:
      return None

    canonical_group = query_result[0]
    visited = set()
    while dict(canonical_group).get('canonical_group'):
      visited.add(canonical_group.key)
      next_group_key = dict(canonical_group).get('canonical_group')
      # Visited check is just precaution.
      # If it is true - the system previously failed to prevent loop creation.
      if next_group_key == current_group_key or next_group_key in visited:
        logging.warning(
            'Alert group auto merge failed. Found a loop while '
            'searching for a canonical group for %r', current_group_key)
        return None
      canonical_group = client.GetEntityByKey(next_group_key)

    return canonical_group.key.name


  @classmethod
  def GetAnomaliesByID(cls, group_id):
    """ Given a group id, return a list of anomaly id.
    """
    client = datastore_client.DataStoreClient()
    group_key = client.AlertGroupKey(group_id)
    group = client.GetEntityByKey(group_key)
    if group:
      return [a.id for a in group.get('anomalies')]
    raise NoEntityFoundException('No Alert Group Found with id: %s', group_id)

  @classmethod
  def Get(cls, group_name, group_type, active=True):
    client = datastore_client.DataStoreClient()
    filters = [
      ('name', '=', group_name)
    ]
    groups = list(client.QueryAlertGroup(active=active, extra_filters=filters))

    return [g for g in groups if g.get('group_type') == group_type]


  @classmethod
  def GetGroupsForAnomaly(
    cls, test_key, start_rev, end_rev, create_on_ungrouped=False, parity=False):
    ''' Find the alert groups for the anomaly.

    Given the test_key and revision range of an anomaly:
    1. find the subscriptions.
    2. for each subscriptions, find the groups for the anomaly.
        if no existing group is found:
         - if create_on_ungrouped is True, create a new group.
         - otherwise, use the 'ungrouped'.
    '''
    client = sheriff_config_client.GetSheriffConfigClient()
    matched_configs, err_msg = client.Match(test_key)

    if err_msg is not None:
      raise SheriffConfigRequestException(err_msg)

    if not matched_configs:
      return []

    start_rev = int(start_rev)
    end_rev = int(end_rev)
    master_name = test_key.split('/')[0]
    benchmark_name = test_key.split('/')[2]

    existing_groups = cls.Get(benchmark_name, 0)
    result_groups = set()
    new_groups = set()
    for config in matched_configs:
      s = config['subscription']
      has_overlapped = False
      for g in existing_groups:
        if (g['domain'] == master_name and
            g['subscription_name'] == s.get('name') and
            g['project_id'] == s.get('monorail_project_id', '') and
            max(g['revision']['start'], start_rev) <= min(g['revision']['end'], end_rev) and
            (abs(g['revision']['start'] - start_rev) + abs(g['revision']['end'] - end_rev) <= 100 or g['domain'] != 'ChromiumPerf')):
          has_overlapped = True
          result_groups.add(g.key.name)
      if not has_overlapped:
        if create_on_ungrouped:
          ds_client = datastore_client.DataStoreClient()
          new_group = ds_client.NewAlertGroup(
            benchmark_name=benchmark_name,
            master_name=master_name,
            subscription_name=s.get('name'),
            group_type=2,
            project_id=s.get('monorail_project_id', ''),
            start_rev=start_rev,
            end_rev=end_rev
          )
          logging.info('Saving new group %s', new_group.key.name)
          if parity:
            new_groups.add(new_group.key.name)
          else:
            ds_client.SaveAlertGroup(new_group)
          result_groups.add(new_group.key.name)
        else:
          # return the id of the 'ungrouped'
          ungrouped = cls._GetUngroupedGroup()
          if ungrouped:
            result_groups.add(ungrouped.key.id)

    logging.debug('GetGroupsForAnomaly returning %s', result_groups)
    return list(result_groups), list(new_groups)


  @classmethod
  def GetAll(cls):
    """Fetch all active alert groups"""
    client = datastore_client.DataStoreClient()

    groups = list(client.QueryAlertGroup())

    return [client.GetEntityKey(g) for g in groups]


  @classmethod
  def _GetUngroupedGroup(cls):
    ''' Get the "ungrouped" group

    The alert_group named "ungrouped" contains the alerts for further
    processing in the next iteration of of dashboard-alert-groups-update
    cron job.
    '''
    ungrouped_groups = cls.Get('Ungrouped', 2)
    ds_client = datastore_client.DataStoreClient()
    if not ungrouped_groups:
      # initiate when there is no active group called 'Ungrouped'.
      new_group = ds_client.NewAlertGroup(
        benchmark_name='Ungrouped',
        group_type=0
      )
      ds_client.SaveAlertGroup(new_group)
      return None
    if len(ungrouped_groups) != 1:
      logging.warning('More than one active groups are named "Ungrouped".')
    ungrouped = ungrouped_groups[0]
    return ungrouped


  @classmethod
  def ProcessUngroupedAlerts(cls):
    """ Process each of the alert which needs a new group

    This alerts are added to the 'ungrouped' group during anomaly detection
    when no existing group is found to add them to.
    """
    IS_PARITY = True
    ungrouped = cls._GetUngroupedGroup()
    if not ungrouped:
      return
    ds_client = datastore_client.DataStoreClient()
    ungrouped_anomalies = ds_client.get_multi(ungrouped.anomalies)
    logging.info('Loaded %s ungrouped alerts from "ungrouped". ID(%s)',
                  len(ungrouped_anomalies), ungrouped.key.id)

    parity_results = {}
    for anomaly in ungrouped_anomalies:
      group_ids, new_ids = cls.GetGroupsForAnomaly(
        anomaly['test'].name, anomaly['start_revision'], anomaly['end_revision'],
        create_on_ungrouped=True, parity=IS_PARITY)
      anomaly['groups'] = [ds_client.AlertGroupKey(group_id) for group_id in group_ids]
      if IS_PARITY:
        anomaly_id = anomaly.key.id
        parity_results[anomaly_id] = {
          "existing_groups": list(set(group_ids) - set(new_ids)),
          "new_groups": new_ids
        }
      else:
        ds_client.SaveAnomaly(anomaly)

    return parity_results
