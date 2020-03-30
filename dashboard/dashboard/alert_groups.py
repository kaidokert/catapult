# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import datetime

from dashboard.common import request_handler
from dashboard.models import alert_group
from google.appengine.ext import ndb


class AlertGroupsHandler(request_handler.RequestHandler):
  """Create, Update and Delete AlterGroups."""

  def get(self):
    groups = alert_group.AlertGroup.GetAll()
    for group in groups:
      group.Update()
      if group.status == alert_group.AlertGroup.Status.untriaged:
        group.TryTriage()
      elif group.status == alert_group.AlertGroup.Status.triaged:
        group.TryBisect()
      else:
        deadline = group.updated + datetime.timedelta(days=7)
        past_due = deadline < datetime.datetime.now()
        closed = (group.status == alert_group.AlertGroup.Status.closed)
        untriaged = (group.status == alert_group.AlertGroup.Status.untriaged)
        if past_due and (closed or untriaged):
          group.Deactive()
    ndb.put_multi(groups)

    def FindGroup(group):
      for g in groups:
        if g.revision.IsOverlapping(group.revision):
          return g.key()
      return None

    ungrouped_list = alert_group.AlertGroup.Get('Ungrouped', None)
    if not ungrouped_list:
      alert_group.AlertGroup(name='Ungrouped', active=True).put()
      return
    ungrouped = ungrouped_list[0]
    for anomaly_entity in ungrouped.anomalies:
      anomaly_entity.groups = [
          FindGroup(g) or g.put()
          for g in alert_group.AlertGroup.GenerateAllGroupsForAnomaly(
              anomaly_entity)
      ]
    ndb.put_multi(ungrouped.anomalies)
