# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import

import datetime
import logging
import uuid

from google.cloud import datastore

from application import utils

class AlertGroupStatus:
  unknown = 0
  untriaged = 1
  triaged = 2
  bisected = 3
  closed = 4

class AlertGroupType:
  ungrouped = 0
  test_suite = 2

class DataStoreClient():
  gae_project_name = 'chromeperf'
  if utils.IsStagingEnvironment():
    gae_project_name = 'chromeperf-stage'
  _client = datastore.Client(project=gae_project_name)


  def _Key(self, kind, id):
    return self._client.key(kind, id)


  def QueryAlertGroup(self, active=True, extra_filters=[], limit=None):
    filters = [('active', '=', active)]
    filters += extra_filters

    query = self._client.query(kind='AlertGroup', filters=filters)

    return query.fetch(limit=limit)


  def AlertGroupKey(self, group_id):
    return self._Key('AlertGroup', group_id)


  def NewAlertGroup(self, benchmark_name, group_type, master_name=None, subscription_name=None,
                    project_id=None, start_rev=None, end_rev=None):
    if group_type == AlertGroupType.ungrouped:
      new_group = datastore.Entity(self._client.key('AlertGroup'))
    elif group_type == AlertGroupType.test_suite:
      new_id = str(uuid.uuid4())
      new_group = datastore.Entity(self._client.key('AlertGroup'), new_id)
    else:
      logging.warning('[PerfIssueService] Unsupported group type: %s', group_type)
      return None

    new_group.update(
        {
           'name': benchmark_name,
           'status' : AlertGroupStatus.untriaged,
           'group_type': group_type,
           'active': True
        }
    )

    if master_name:
      new_group['domain'] = master_name
    if subscription_name:
      new_group['subscription_name'] = subscription_name
    if project_id:
      new_group['project_id'] = project_id
    if start_rev and end_rev:
      new_revision = datastore.Entiry()
      new_revision.update(
        {
          'repository': 'chromium',
          'start': start_rev,
          'end': end_rev
        }
      )
      new_group['revision'] = new_revision

    return new_group


  def SaveAlertGroup(self, group):
    time_stamp = datetime.datetime.now(tz=datetime.timezone.utc)
    if not group.get('created'):
      group['created'] = time_stamp
    group['updated'] = time_stamp

    return self._client.put(group)


  def SaveAnomaly(self, anomaly):
    return self._client.put(anomaly)


  def GetEntityByKey(self, key):
     return self._client.get(key)


  def GetEntityKey(self, entity, key_type=None):
    if key_type == 'id':
        return entity.key.id
    if key_type == 'name':
        return entity.key.name
    return entity.key.id_or_name


