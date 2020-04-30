# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The database model for an "Anomaly", which represents a step up or down."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import datetime
import logging
import os
import uuid

import jinja2

from dashboard import sheriff_config_client
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.services import issue_tracker_service
from google.appengine.ext import ndb


class RevisionRange(ndb.Model):
  repository = ndb.StringProperty()
  start = ndb.IntegerProperty()
  end = ndb.IntegerProperty()

  def IsOverlapping(self, b):
    if not b or self.repository != b.repository:
      return False
    return max(self.start, b.start) < min(self.end, b.end)


class BugInfo(ndb.Model):
  project = ndb.StringProperty()
  bug_id = ndb.IntegerProperty()


class AlertGroup(ndb.Model):
  name = ndb.StringProperty(indexed=True)
  created = ndb.DateTimeProperty(indexed=False, auto_now_add=True)
  updated = ndb.DateTimeProperty(indexed=False, auto_now_add=True)

  class Status(object):
    unknown = 0
    untriaged = 1
    triaged = 2
    bisected = 3
    closed = 4

  status = ndb.IntegerProperty(indexed=False)
  active = ndb.BooleanProperty(indexed=True)
  revision = ndb.LocalStructuredProperty(RevisionRange)
  bug = ndb.LocalStructuredProperty(BugInfo)
  bisection_ids = ndb.StringProperty(repeated=True)
  anomalies = ndb.KeyProperty(repeated=True)

  @classmethod
  def GenerateAllGroupsForAnomaly(cls, anomaly_entity):
    # TODO(fancl): Support multiple group name
    return [cls(
        id=str(uuid.uuid4()),
        name=anomaly_entity.benchmark_name,
        status=cls.Status.untriaged,
        active=True,
        revision=RevisionRange(
            repository='chromium',
            start=anomaly_entity.start_revision,
            end=anomaly_entity.end_revision,
        ),
    )]

  @classmethod
  def GetGroupsForAnomaly(cls, anomaly_entity):
    # TODO(fancl): Support multiple group name
    name = anomaly_entity.benchmark_name
    revision = RevisionRange(
        repository='chromium',
        start=anomaly_entity.start_revision,
        end=anomaly_entity.end_revision,
    )
    groups = cls.Get(name, revision) or cls.Get('Ungrouped', None)
    return [g.key for g in groups]

  @classmethod
  def GetByID(cls, group_id):
    return ndb.Key('AlertGroup', group_id).get()

  @classmethod
  def Get(cls, group_name, revision_info, active=True):
    query = cls.query(
        cls.active == active,
        cls.name == group_name,
    )
    if not revision_info:
      return list(query.fetch())
    return [group for group in query.fetch()
            if revision_info.IsOverlapping(group.revision)]

  @classmethod
  def GetAll(cls, active=True):
    return list(cls.query(cls.active == active).fetch())

  def Update(self):
    anomalies = anomaly.Anomaly.query(anomaly.Anomaly.groups.IN([self.key]))
    self.anomalies = [a.key for a in anomalies.fetch()]
    # TODO(fancl): Fetch issue status

  def TryTriage(self):
    self.bug = self._TryFileBug()
    if not self.bug:
      return
    self.updated = self.updated = datetime.datetime.now()
    self.status = self.Status.triaged

  def TryBisect(self):
    # TODO(fancl): Trigger bisection
    pass

  def Archive(self):
    self.active = False

  @staticmethod
  def _GetPreproccessedRegressions(anomalies):
    regressions = [a for a in anomalies if not a.is_improvement]
    sheriff_config = sheriff_config_client.GetSheriffConfigClient()
    subscriptions_dict = {}
    for a in regressions:
      response, _ = sheriff_config.Match(a.test.string_id(), check=True)
      subscriptions_dict.update({s.name: s for s in response})
      a.auto_triage_enable = any(s.auto_triage_enable for s in response)
    subscriptions = subscriptions_dict.values()
    return (regressions, subscriptions)

  def _TryFileBug(self):
    anomalies = ndb.get_multi(self.anomalies)
    regressions, subscriptions = self._GetPreproccessedRegressions(anomalies)
    if not regressions or not any(s.auto_triage_enable for s in subscriptions):
      return None

    regressions.sort(
        key=lambda x: x.median_after_anomaly / x.median_before_anomaly)
    benchmark_tuple = collections.namedtuple(
        '_Benchmark', ['name', 'owners']
    )
    benchmarks_dict = dict()
    for a in anomalies:
      name = a.benchmark_name
      benchmarks_dict[name] = (benchmarks_dict.get(name, []) +
                               a.ownership.get('emails') if a.ownership else [])
    benchmarks = [benchmark_tuple(name, list(set(owners)))
                  for name, owners in benchmarks_dict.items()]
    env = {'group': self, 'regressions': regressions, 'benchmarks': benchmarks}
    description = _BugDetails(env)
    title = _BugTitle(env)

    issue_tracker = _IssueTracker()
    # TODO(fancl): Fix legacy bug components in labels
    components = set(c for s in subscriptions for c in s.bug_components)
    cc = set(e for s in subscriptions for e in s.bug_cc_emails)
    labels = set(l for s in subscriptions for l in s.bug_labels)
    response = issue_tracker.NewBug(
        title, description, labels=labels, components=components, cc=cc)
    if 'error' in response:
      logging.warning('AlertGroup file bug failed: %s', response['error'])
      return None

    # TODO(fancl): Remove legacy bug_id info in alerts
    for a in regressions:
      if not a.bug_id and a.auto_triage_enable:
        a.bug_id = response['bug_id']
    ndb.put_multi(regressions)
    # TODO(fancl): Add bug project in config
    return BugInfo(project='chromium', bug_id=response['bug_id'])


def _BugTitle(env):
  return jinja2.Template(
      'Chromeperf Alerts: '
      '{{ regressions|length }} regressions in {{ group.name }}'
  ).render(env)


_TEMPLATE_LOADER = jinja2.FileSystemLoader(
    searchpath=os.path.dirname(os.path.realpath(__file__)))
_TEMPLATE_ENV = jinja2.Environment(loader=_TEMPLATE_LOADER)


def _BugDetails(env):
  return _TEMPLATE_ENV.get_template(
      'alert_groups_bug_description.j2').render(env)


def _IssueTracker():
  return issue_tracker_service.IssueTrackerService(
      utils.ServiceAccountHttp())
