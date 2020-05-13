# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""The database model for an "Anomaly", which represents a step up or down."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import datetime
import json
import logging
import os
import uuid

import jinja2

from dashboard import pinpoint_request
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import subscription
from dashboard.services import issue_tracker_service
from dashboard.services import pinpoint_service
from google.appengine.ext import ndb

# Move import of protobuf-dependent code here so that all AppEngine work-arounds
# have a chance to be live before we import any proto code.
from dashboard import sheriff_config_client

# Templates used for rendering issue contents
_TEMPLATE_LOADER = jinja2.FileSystemLoader(
    searchpath=os.path.dirname(os.path.realpath(__file__)))
_TEMPLATE_ENV = jinja2.Environment(loader=_TEMPLATE_LOADER)
_TEMPLATE_ISSUE_TITLE = jinja2.Template(
    'Chromeperf Alerts: '
    '{{ regressions|length }} regressions in {{ group.name }}')
_TEMPLATE_ISSUE_CONTENT = _TEMPLATE_ENV.get_template(
    'alert_groups_bug_description.j2')
_TEMPLATE_ISSUE_COMMENT = _TEMPLATE_ENV.get_template(
    'alert_groups_bug_comment.j2')


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


class BugUpdateDetails(
    collections.namedtuple('BugUpdateDetails', ('components', 'cc', 'labels'))):
  __slots__ = ()


class BenchmarkDetails(
    collections.namedtuple('BenchmarkDetails',
                           ('name', 'bot', 'owners', 'regressions'))):
  __slots__ = ()


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

  def IsOverlapping(self, b):
    return self.name == b.name and self.revision.IsOverlapping(b.revision)

  @classmethod
  def GenerateAllGroupsForAnomaly(cls, anomaly_entity):
    # TODO(fancl): Support multiple group name
    return [
        cls(
            id=str(uuid.uuid4()),
            name=anomaly_entity.benchmark_name,
            status=cls.Status.untriaged,
            active=True,
            revision=RevisionRange(
                repository='chromium',
                start=anomaly_entity.start_revision,
                end=anomaly_entity.end_revision,
            ),
        )
    ]

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
    return [
        group for group in query.fetch()
        if revision_info.IsOverlapping(group.revision)
    ]

  @classmethod
  def GetAll(cls, active=True):
    groups = cls.query(cls.active == active).fetch()
    return groups or []

  def Update(self, now, active_window, triage_delay):
    added = self._UpdateAnomalies()
    if (self.status == self.Status.triaged or
        self.status == self.Status.bisected):
      self._UpdateIssue(added)
      self._UpdateStatus()

    # Trigger actions
    if self.updated + active_window < now and (
        self.status == self.Status.closed or
        self.status == self.Status.untriaged):
      self._Archive()
    elif self.created + triage_delay < now and (
        self.status == self.Status.untriaged):
      self._TryTriage()
    elif self.status == self.Status.triaged:
      self._TryBisect()

  def _UpdateAnomalies(self):
    anomalies = anomaly.Anomaly.query(anomaly.Anomaly.groups.IN([self.key
                                                                ])).fetch()
    added = [a for a in anomalies if a.key not in self.anomalies]
    self.anomalies = [a.key for a in anomalies]
    return added

  def _UpdateStatus(self):
    issue = _IssueTracker().GetIssue(self.bug.bug_id)
    if issue and issue.get('state') == 'closed':
      self.status = self.Status.closed

  def _UpdateIssue(self, added):
    regressions, subscriptions = self._GetPreproccessedRegressions(added)
    # Only update issue if there is at least one regression
    if not regressions or not any(s.auto_triage_enable for s in subscriptions):
      return None

    for regression in regressions:
      if not regression.bug_id and regression.auto_triage_enable:
        regression.bug_id = self.bug.bug_id

    # Write back bug_id to regressions. We can't do it when anomaly is
    # found because group may being updating at that time.
    ndb.put_multi(regressions)

    template_args = self._GetTemplateArgs(regressions)
    comment = _TEMPLATE_ISSUE_COMMENT.render(template_args)
    components, cc, labels = self._ComputeBugUpdate(subscriptions, regressions)
    _IssueTracker().AddBugComment(
        self.bug.bug_id,
        comment,
        labels=labels,
        cc_list=cc,
        components=components)

  def _TryTriage(self):
    bug, anomalies = self._FileIssue()
    if not bug:
      return

    # Update the issue associated with his group, before we continue.
    self.bug = bug
    self.updated = datetime.datetime.now()
    self.status = self.Status.triaged
    self.put()

    # Link the bug to auto-triage enabled anomalies.
    for a in anomalies:
      if not a.bug_id and a.auto_triage_enable:
        # TODO(dberris): Add bug project in config and anomaly
        a.bug_id = self.bug.bug_id
    ndb.put_multi(anomalies)

  def _TryBisect(self):
    job_id, anomalies = self._NewPinpointBisect()
    if not job_id:
      return

    # Update the issue associated with his group, before we continue.
    self.bisection_ids.append(job_id)
    self.updated = datetime.datetime.now()
    self.status = self.Status.bisected
    self.put()

    # Link the bug to auto-bisect enabled anomalies.
    for a in anomalies:
      if a.auto_bisect_enable:
        a.pinpoint_bisects.append(job_id)
    ndb.put_multi(anomalies)

  def _Archive(self):
    self.active = False

  @staticmethod
  def _GetPreproccessedRegressions(anomalies):
    regressions = []
    sheriff_config = sheriff_config_client.GetSheriffConfigClient()
    subscriptions_dict = {}
    for a in anomalies:
      subscriptions, _ = sheriff_config.Match(a.test.string_id(), check=True)
      subscriptions_dict.update({s.name: s for s in subscriptions})
      # Only auto-triage if this is a regression.
      a.auto_triage_enable = any(s.auto_triage_enable for s in subscriptions)
      a.auto_bisect_enable = any(s.auto_bisect_enable for s in subscriptions)
      a.relative_delta = abs(a.absolute_delta / float(a.median_before_anomaly)
                            ) if a.median_before_anomaly != 0. else float('Inf')
      if not a.is_improvement and not a.recovered:
        regressions.append(a)
    return (regressions, subscriptions_dict.values())

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

  @classmethod
  def _GetBenchmarksFromRegressions(cls, regressions):
    benchmarks_dict = dict()
    for regression in regressions:
      name = regression.benchmark_name
      benchmark = benchmarks_dict.get(
          name, BenchmarkDetails(name, regression.bot_name, set(), []))
      if regression.ownership:
        emails = regression.ownership.get('emails') or []
        benchmark.owners.update(emails)
      benchmark.regressions.append(regression)
      benchmarks_dict[name] = benchmark
    return benchmarks_dict.values()

  def _GetTemplateArgs(self, regressions):
    # Preparing template arguments used in rendering issue's title and content.
    regressions.sort(key=lambda x: x.relative_delta, reverse=True)
    benchmarks = self._GetBenchmarksFromRegressions(regressions)
    return {
        # Current AlertGroup used for rendering templates
        'group': self,

        # Performance regressions sorted by relative difference
        'regressions': regressions,

        # Benchmarks that occur in regressions, including names and owners
        'benchmarks': benchmarks,

        # Parse the real unit (remove things like smallerIsBetter)
        'parse_unit': lambda s: (s or '').rsplit('_', 1)[0],
    }

  def _ComputeBugUpdate(self, subscriptions, regressions):
    components = list(
        set(c for s in subscriptions for c in s.bug_components)
        | self._GetComponentsFromRegressions(regressions))
    cc = list(set(e for s in subscriptions for e in s.bug_cc_emails))
    labels = list(
        set(l for s in subscriptions for l in s.bug_labels)
        | set(['Chromeperf-Auto-Triaged']))
    # We layer on some default labels if they don't conflict with any of the
    # provided ones.
    if not any(l.startswith('Pri-') for l in labels):
      labels.append('Pri-2')
    if not any(l.startswith('Type-') for l in labels):
      labels.append('Type-Bug-Regression')
    if any(s.visibility == subscription.VISIBILITY.INTERNAL_ONLY
           for s in subscriptions):
      labels = list(set(labels) | set(['Restrict-View-Google']))
    return BugUpdateDetails(components, cc, labels)

  def _FileIssue(self):
    anomalies = ndb.get_multi(self.anomalies)
    regressions, subscriptions = self._GetPreproccessedRegressions(anomalies)
    # Only file a issue if there is at least one regression
    # We can't use subsciptions' auto_triage_enable here because it's
    # merged across anomalies.
    if not any(r.auto_triage_enable for r in regressions):
      return None

    template_args = self._GetTemplateArgs(regressions)
    # Rendering issue's title and content
    title = _BugTitle(template_args)
    description = _BugDetails(template_args)

    # Fetching issue labels, components and cc from subscriptions and owner
    issue_tracker = _IssueTracker()
    components, cc, labels = self._ComputeBugUpdate(subscriptions, regressions)

    response = issue_tracker.NewBug(
        title, description, labels=labels, components=components, cc=cc)
    if 'error' in response:
      logging.warning('AlertGroup file bug failed: %s', response['error'])
      return None

    # TODO(dberris): Add bug project in config and anomaly
    return BugInfo(project='chromium', bug_id=response['bug_id']), anomalies

  def _NewPinpointBisect(self):
    anomalies = ndb.get_multi(self.anomalies)
    regressions, _ = self._GetPreproccessedRegressions(anomalies)
    regression = max(regressions, key=lambda r: r.relative_delta)

    request = _GetPinpointRequest(regression)
    logging.info('Pinpoint request: %s', request)

    results = pinpoint_service.NewJob(request)
    logging.info('Pinpoint Service Response: %s', results)

    return results.get('jobId'), anomalies


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


def _GetPinpointRequest(alert):
  if not hasattr(_GetPinpointRequest, 'user'):
    _GetPinpointRequest.user = utils.ServiceAccountEmail()
  user = _GetPinpointRequest.user

  test_path = alert.test.string_id()
  test = alert.test.get()

  story = test.unescaped_story_name
  grouping_label, chart_name, trace_name = (
      pinpoint_request.ParseGroupingLabelChartNameAndTraceName(test_path))

  start_git_hash = pinpoint_request.ResolveToGitHash(
      alert.end_revision, alert.benchmark_name)
  end_git_hash = pinpoint_request.ResolveToGitHash(
      alert.start_revision, alert.benchmark_name)

  # Pinpoint also requires you specify which isolate target to run the
  # test, so we derive that from the suite name. Eventually, this would
  # ideally be stored in a SparesDiagnostic but for now we can guess.
  target = pinpoint_request.GetIsolateTarget(
      alert.bot_name, alert.benchmark_name,
      alert.start_revision, alert.end_revision)

  job_name = 'Auto-Bisection on %s/%s' % (alert.bot_name, alert.benchmark_name)

  # Histogram names don't include the statistic, so split these
  chart_name, statistic_name = (
      pinpoint_request.ParseStatisticNameFromChart(chart_name))

  alert_magnitude = alert.median_after_anomaly - alert.median_before_anomaly

  return {
      'configuration': alert.bot_name,
      'benchmark': alert.benchmark_name,
      'story': story,
      'start_git_hash': start_git_hash,
      'end_git_hash': end_git_hash,
      'bug_id': alert.bug_id,
      'comparison_mode': 'performance',
      'comparison_magnitude': alert_magnitude,
      'target': target,
      'user': user,
      'name': job_name,
      'statistic': statistic_name,
      'grouping_label': grouping_label,
      'trace': trace_name,
      'priority': 10,
      'tags': json.dumps({
          'test_path': test_path,
          'alert': alert.key(),
          'auto_bisection': True,
      }),
  }
