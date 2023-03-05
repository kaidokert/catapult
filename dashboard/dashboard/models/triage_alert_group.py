from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import jinja2
import logging

from google.appengine.ext import ndb

from dashboard import revision_info_client
from dashboard.models import alert_group
from dashboard.models import subscription
from dashboard.services import issue_tracker_service

_TEMPLATE_LOADER = jinja2.FileSystemLoader(
    searchpath=os.path.join(os.path.dirname(os.path.realpath(__file__))))
_TEMPLATE_ENV = jinja2.Environment(loader=_TEMPLATE_LOADER)
_TEMPLATE_ISSUE_TITLE = jinja2.Template(
    '[{{ group.subscription_name }}]: '
    '{{ regressions|length }} regressions in {{ group.name }}')
_TEMPLATE_ISSUE_CONTENT = _TEMPLATE_ENV.get_template(
    'alert_groups_bug_description.j2')

class AlertGroupTriage:

  class BenchmarkDetails(
      collections.namedtuple('BenchmarkDetails',
                             ('name', 'owners', 'regressions', 'info_blurb'))):
    __slots__ = ()

  def __init__(self, group, update, verification=None):
    self._group = group
    self._update = update
    self._verification = verification
    self._issue_tracker = _IssueTracker()
    self._revision_info = revision_info_client

  def TryTriage(self):
    if self._verification.decision == True:
      self._Triage()
    else:
      return

  def _Triage(self):
    bug, anomalies = self._FileIssue(self._update.anomalies)
    if not bug:
      return

    # Update the issue associated with his group, before we continue.
    self._group.bug = bug
    self._group.updated = self._update.now
    self._group.status = self._group.Status.triaged
    self._CommitGroup()

    # Link the bug to auto-triage enabled anomalies.
    for a in anomalies:
      if a.bug_id is None and a.auto_triage_enable:
        a.project_id = bug.project
        a.bug_id = bug.bug_id
    ndb.put_multi(anomalies)

  def _FileIssue(self, anomalies):
    regressions, subscriptions = self._GetRegressions(anomalies)
    # Only file a issue if there is at least one regression
    # We can't use subsciptions' auto_triage_enable here because it's
    # merged across anomalies.
    if not any(r.auto_triage_enable for r in regressions):
      return None, []

    auto_triage_regressions = []
    for r in regressions:
      if r.auto_triage_enable:
        auto_triage_regressions.append(r)
    logging.info('auto_triage_enabled due to %s', auto_triage_regressions)

    template_args = self._GetTemplateArgs(regressions)
    top_regression = template_args['regressions'][0]
    template_args['revision_infos'] = self._revision_info.GetRangeRevisionInfo(
        top_regression.test,
        top_regression.start_revision,
        top_regression.end_revision,
    )
    # Rendering issue's title and content
    title = _TEMPLATE_ISSUE_TITLE.render(template_args)
    description = _TEMPLATE_ISSUE_CONTENT.render(template_args)

    # Fetching issue labels, components and cc from subscriptions and owner
    components, cc, labels = self._ComputeBugUpdate(subscriptions, regressions)
    logging.info('Creating a new issue for AlertGroup %s', self._group.key)

    response = self._issue_tracker.NewBug(
        title,
        description,
        labels=labels,
        components=components,
        cc=cc,
        project=self._group.project_id)
    if 'error' in response:
      logging.warning('AlertGroup file bug failed: %s', response['error'])
      return None, []

    # Update the issue associated witht his group, before we continue.
    return alert_group.BugInfo(
        project=self._group.project_id,
        bug_id=response['bug_id'],
    ), anomalies

  def _GetRegressions(self, anomalies):
    regressions = []
    subscriptions_dict = {}
    for a in anomalies:
      logging.info(
          'GetRegressions: auto_triage_enable is %s for anomaly %s due to subscription: %s',
          a.auto_triage_enable,
          a.test.string_id(),
          [s.name for s in a.subscriptions])

      subscriptions_dict.update({s.name: s for s in a.subscriptions})
      if not a.is_improvement and not a.recovered and a.auto_triage_enable:
        regressions.append(a)
    return (regressions, list(subscriptions_dict.values()))

  def _GetTemplateArgs(self, regressions):
    # Preparing template arguments used in rendering issue's title and content.
    regressions.sort(key=lambda x: x.relative_delta, reverse=True)
    benchmarks = self._GetBenchmarksFromRegressions(regressions)
    return {
        # Current AlertGroup used for rendering templates
        'group': self._group,

        # Performance regressions sorted by relative difference
        'regressions': regressions,

        # Benchmarks that occur in regressions, including names, owners, and
        # information blurbs.
        'benchmarks': benchmarks,

        # Parse the real unit (remove things like smallerIsBetter)
        'parse_unit': lambda s: (s or '').rsplit('_', 1)[0],
    }

  @classmethod
  def _GetBenchmarksFromRegressions(cls, regressions):
    benchmarks_dict = dict()
    for regression in regressions:
      name = regression.benchmark_name
      emails = []
      info_blurb = None
      if regression.ownership:
        emails = regression.ownership.get('emails') or []
        info_blurb = regression.ownership.get('info_blurb') or ''
      benchmark = benchmarks_dict.get(
          name, cls.BenchmarkDetails(name, list(set(emails)), list(),
                                     info_blurb))
      benchmark.regressions.append(regression)
      benchmarks_dict[name] = benchmark
    return list(benchmarks_dict.values())

  def _ComputeBugUpdate(self, subscriptions, regressions):
    components = list(
        set(c for s in subscriptions for c in s.bug_components)
        | self._GetComponentsFromRegressions(regressions))
    cc = list(set(e for s in subscriptions for e in s.bug_cc_emails))
    labels = list(
        set(l for s in subscriptions for l in s.bug_labels)
        | {'Chromeperf-Auto-Triaged'})
    # We layer on some default labels if they don't conflict with any of the
    # provided ones.
    if not any(l.startswith('Pri-') for l in labels):
      labels.append('Pri-2')
    if not any(l.startswith('Type-') for l in labels):
      labels.append('Type-Bug-Regression')
    if any(s.visibility == subscription.VISIBILITY.INTERNAL_ONLY
           for s in subscriptions):
      labels = list(set(labels) | {'Restrict-View-Google'})
    return self.BugUpdateDetails(components, cc, labels)

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

  def _CommitGroup(self):
    return self._group.put()


def _IssueTracker():
  """Get a cached IssueTracker instance."""
  # pylint: disable=protected-access
  if not hasattr(_IssueTracker, '_client'):
    _IssueTracker._client = issue_tracker_service.IssueTrackerService()
  return _IssueTracker._client
