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

# Templates used for rendering issue contents
_TEMPLATE_LOADER = jinja2.FileSystemLoader(
    searchpath=os.path.dirname(os.path.realpath(__file__)))
_TEMPLATE_ENV = jinja2.Environment(loader=_TEMPLATE_LOADER)
_TEMPLATE_ISSUE_TITLE = jinja2.Template(
    'Chromeperf Alerts: '
    '{{ regressions|length }} regressions in {{ group.name }}'
)
_TEMPLATE_ISSUE_CONTENT = _TEMPLATE_ENV.get_template(
    'alert_groups_bug_description.j2')


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
    self.bug = self._FileIssue()
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

  @staticmethod
  def _GetComponentsFromRegressions(regressions):
    components = []
    for r in regressions:
      component = r.ownership and r.ownership.get('component')
      if not component:
        continue
      if isinstance(component, list) and component:
        components.append(component[0])
      elif component:
        components.append(component)
    return set(components)

  @staticmethod
  def _GetBenchmarksFromRegressions(regressions):
    benchmark_tuple = collections.namedtuple(
        '_Benchmark', ['name', 'owners', 'regressions']
    )
    benchmarks_dict = dict()
    for r in regressions:
      name = r.benchmark_name
      b = benchmarks_dict.get(name, benchmark_tuple(name, set(), []))
      if r.ownership:
        b.owners.update(r.ownership.get('emails', []))
      b.regressions.append(r)
      benchmarks_dict[name] = b
    return benchmarks_dict.values()


  def _FileIssue(self):
    anomalies = ndb.get_multi(self.anomalies)
    regressions, subscriptions = self._GetPreproccessedRegressions(anomalies)
    # Only file a issue if there is at least one regression
    if not regressions or not any(s.auto_triage_enable for s in subscriptions):
      return None

    # Preparing template arguments used in rendering issue's title and content.
    regressions.sort(
        key=lambda x: - x.median_after_anomaly / x.median_before_anomaly)
    benchmarks = self._GetBenchmarksFromRegressions(regressions)
    template_args = {
        # Current AlertGroup used for rendering templates
        'group': self,
        # Performance regressions sorted by relative difference
        'regressions': regressions,
        # Benchmarks occur in regressions, including names and owners
        'benchmarks': benchmarks,
    }
    # Rendering issue's title and content
    title = _BugTitle(template_args)
    description = _BugDetails(template_args)

    # Fetching issue labels, components and cc from subscriptions and owner
    issue_tracker = _IssueTracker()
    # TODO(fancl): Fix legacy bug components in labels
    components = (
        set(c for s in subscriptions for c in s.bug_components) |
        self._GetComponentsFromRegressions(regressions)
    )
    cc = set(e for s in subscriptions for e in s.bug_cc_emails)
    labels = (
        set(l for s in subscriptions for l in s.bug_labels) |
        set(['Chromeperf-Auto-Triaged'])
    )
    response = issue_tracker.NewBug(
        title, description, labels=labels, components=components, cc=cc)
    if 'error' in response:
      logging.warning('AlertGroup file bug failed: %s', response['error'])
      return None

    # Link the bug to auto-triage enabled alerts.
    # TODO(fancl): Remove legacy bug_id info in alerts
    for a in regressions:
      if not a.bug_id and a.auto_triage_enable:
        a.bug_id = response['bug_id']
    ndb.put_multi(regressions)
    # TODO(fancl): Add bug project in config
    return BugInfo(project='chromium', bug_id=response['bug_id'])


def _BugTitle(env):
  return _TEMPLATE_ISSUE_TITLE.render(env)


def _BugDetails(env):
  return _TEMPLATE_ISSUE_CONTENT.render(env)


def _IssueTracker():
  """Get a cached IssueTracker instance."""
  # pylint: disable=protected-access
  if not hasattr(_IssueTracker, '_client'):
    _IssueTracker._client = issue_tracker_service.IssueTrackerService(
        utils.ServiceAccountHttp())
  return _IssueTracker._client
