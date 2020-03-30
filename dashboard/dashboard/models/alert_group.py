# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The database model for an "Anomaly", which represents a step up or down."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import datetime
import json
import logging

from dashboard import sheriff_config_client
from dashboard import short_uri
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.services import issue_tracker_service
from google.appengine.api import app_identity
from google.appengine.ext import ndb


class RevisionInfo(ndb.Model):
  repository = ndb.StringProperty()
  start = ndb.IntegerProperty()
  end = ndb.IntegerProperty()

  def IsIntersected(self, b):
    if self.repository != b.repository:
      return False
    return max(self.start, b.start) < min(self.end, b.end)


class BugInfo(ndb.Model):
  project = ndb.StringProperty()
  bug_id = ndb.IntegerProperty()


class AlertGroup(ndb.Model):
  name = ndb.StringProperty(indexed=True)
  created = ndb.DateTimeProperty(indexed=False, auto_now_add=True)
  updated = ndb.DateTimeProperty(indexed=False)

  class Status(object):
    unknown = 0
    untriaged = 1
    triaged = 2
    bisected = 3
    closed = 4

  status = ndb.IntegerProperty(indexed=False)
  active = ndb.BooleanProperty(indexed=True)
  revision = ndb.LocalStructuredProperty(RevisionInfo)
  bug = ndb.LocalStructuredProperty(BugInfo)
  bisection_ids = ndb.StringProperty(repeated=True)
  anomalies = ndb.KeyProperty(repeated=True)

  @classmethod
  def GenerateAllGroupsForAnomaly(cls, anomaly_entity):
    pass

  @classmethod
  def GetGroupsForAnomaly(cls, anomaly_entity):
    # TODO(fancl): Support multiple group name
    name = anomaly_entity.benchmark_name
    revision = RevisionInfo(
        repository='chromium',
        start=anomaly_entity.start_revision,
        end=anomaly_entity.end_revision,
    )
    groups = cls.Get(name, revision) or cls.Get('Ungrouped', None)
    return [g.key for g in groups]

  @classmethod
  def Get(cls, group_name, revision_info, active=True):
    query = cls.query()
    query.filter(cls.active == active)
    query.filter(cls.name == group_name)
    if not revision_info:
      return list(query.fetch())
    return [group for group in query.fetch()
            if revision_info.IsIntersected(group.revision)]

  @classmethod
  def GetAll(cls, active=True):
    return list(cls.query(cls.active == active).fetch())

  def Update(self):
    anomalies = anomaly.Anomaly.query(anomaly.Anomaly.IN([self.key]))
    self.anomalies = anomalies
    # TODO(fancl): Fetch issue status

  def TryTriage(self):
    self.bug = _TryFileBug(self)
    if self.bug:
      return
    self.updated = self.updated = datetime.datetime.now()
    self.status = self.Status.triaged

  def TryBisect(self):
    pass

  def Deactive(self):
    self.active = False


def _TryFileBug(group):
  anomalies = ndb.get_multi(group.anomalies)
  alerts = [a for a in anomalies if not a.is_improvement]
  description = _BugDetails(alerts)
  summary = _BugSummary(alerts)

  sheriff_config = sheriff_config_client.GetSheriffConfigClient()
  subscriptions = [s for a in alerts
                   for s in sheriff_config.Match(a.test.string_id())]
  if not any(s.auto_triage_enable for s in subscriptions):
    return None
  issue_tracker = issue_tracker_service.IssueTrackerService(
      utils.ServiceAccountHttp())
  # TODO(fancl): Fix legacy bug components in labels
  components = set(c for s in subscriptions for c in s.bug_components)
  cc = set(e for s in subscriptions for e in s.bug_cc_emails)
  labels = set(l for s in subscriptions for l in s.bug_labels)
  resp = issue_tracker.NewBug(
      summary, description, labels=labels, components=components, cc=cc)
  if 'error' in resp:
    logging.warning('AlertGroup file bug failed: %s', resp['error'])
    return None

  # TODO(fancl): Remove legacy bug_id info in alerts
  for a in alerts:
    if not a.bug_id:
      a.bug_id = resp['bug_id']
  ndb.put_multi(alerts)
  # TODO(fancl): Add bug project in config
  return BugInfo(project='chromium', bug_id=resp['bug_id'])


def _BugSummary(alerts):
  a = max(alerts, key=lambda x: x.segment_size_after / x.segment_size_before)
  return '%.1f regression in %s at %d:%d ' % (
      a.segment_size_after / a.segment_size_before,
      a.benchmark_name, a.start_revision, a.end_revision
  )


def _BugDetails(alerts):
  base_url = 'https://%s/group_report' % (
      app_identity.get_default_version_hostname())
  # TODO(fancl): User AlertGroup id instead
  sid = short_uri.GetOrCreatePageState(
      json.dumps([a.key.urlsafe() for a in alerts]))
  alerts_url = '%s?sid=%s' % (base_url, sid)
  details = '<b>All graphs for this bug:</b>\n  %s\n\n' % alerts_url
  bot_names = {a.bot_name for a in alerts}
  if bot_names:
    details += '\n\nBot(s) for this bug\'s original alert(s):\n\n'
    details += '\n'.join(sorted(bot_names))
  else:
    details += '\nCould not extract bot names from the list of alerts.'
  return details
