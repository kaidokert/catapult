# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import datetime

from dashboard.common import testing_common
from dashboard.common import utils
from dashboard.models import alert_group
from dashboard.models import alert_group_workflow
from dashboard.models import anomaly
from dashboard.models import subscription
from google.appengine.ext import ndb


class FakeIssueTrackerService(object):
  """A fake version of IssueTrackerService that saves call values."""

  bug_id = 12345
  new_bug_args = None
  new_bug_kwargs = None
  add_comment_args = None
  add_comment_kwargs = None

  def __init__(self, http=None):
    pass

  @classmethod
  def NewBug(cls, *args, **kwargs):
    cls.new_bug_args = args
    cls.new_bug_kwargs = kwargs
    return {'bug_id': cls.bug_id}

  @classmethod
  def AddBugComment(cls, *args, **kwargs):
    cls.add_comment_args = args
    cls.add_comment_kwargs = kwargs
    # If we fined that one of the keyword arguments is an update, we'll mimic
    # what the actual service will do and mark the state "closed" or "open".
    if kwargs.get('status') in {'WontFix', 'Fixed'}:
      cls.issue['state'] = 'closed'
    else:
      cls.issue['state'] = 'open'

  issue = {
      'cc': [{
          'kind': 'monorail#issuePerson',
          'htmlLink': 'https://bugs.chromium.org/u/1253971105',
          'name': 'user@chromium.org',
      }, {
          'kind': 'monorail#issuePerson',
          'name': 'hello@world.org',
      }],
      'labels': [
          'Type-Bug',
          'Pri-3',
          'M-61',
      ],
      'owner': {
          'kind': 'monorail#issuePerson',
          'htmlLink': 'https://bugs.chromium.org/u/49586776',
          'name': 'owner@chromium.org',
      },
      'id': 737355,
      'author': {
          'kind': 'monorail#issuePerson',
          'htmlLink': 'https://bugs.chromium.org/u/49586776',
          'name': 'author@chromium.org',
      },
      'state': 'closed',
      'status': 'Fixed',
      'summary': 'The bug title',
      'components': [
          'Blink>ServiceWorker',
          'Foo>Bar',
      ],
      'published': '2017-06-28T01:26:53',
      'updated': '2018-03-01T16:16:22',
  }

  @classmethod
  def GetIssue(cls, _):
    return cls.issue


class FakeSheriffConfigClient(object):

  def __init__(self, match):
    self._match = match

  def Match(self, path, **kargs):
    # pylint: disable=unused-argument
    return self._match.get(path, []), None


def AddAnomaly(**kargs):
  default = {
      'test': 'master/bot/test_suite/measurement/test_case',
      'start_revision': 0,
      'end_revision': 100,
      'is_improvement': False,
      'median_before_anomaly': 1.1,
      'median_after_anomaly': 1.3,
      'ownership': {
          'component': 'Foo>Bar',
          'emails': ['x@google.com', 'y@google.com'],
      },
  }
  default.update(kargs)
  default['test'] = utils.TestKey(default['test'])
  return anomaly.Anomaly(**default).put()


def AddAlertGroup(anomaly_key, issue=None, anomalies=None, status=None):
  group = alert_group.AlertGroup.GenerateAllGroupsForAnomaly(
      anomaly_key.get())[0]
  if issue:
    group.bug = alert_group.BugInfo(
        bug_id=issue.get('id'),
        project='chromium',
    )
  if anomalies:
    group.anomalies = anomalies
  if status:
    group.status = status
  return group.put()


class AlertGroupWorkflowTest(testing_common.TestCase):

  def setUp(self):
    super(AlertGroupWorkflowTest, self).setUp()
    self.maxDiff = None

  def testAddAnomalies_GroupUntriaged(self):
    anomalies = [AddAnomaly(), AddAnomaly()]
    added = [AddAnomaly(), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        anomalies=anomalies
    )
    sheriff = subscription.Subscription(name='sheriff')
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies + added),
        issue={},
    ))

    self.assertEqual(len(group.get().anomalies), 4)
    for a in added:
      self.assertIn(a, group.get().anomalies)

  def testAddAnomalies_GroupTriaged_IssueOpen(self):
    anomalies = [AddAnomaly(), AddAnomaly()]
    added = [AddAnomaly(), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        issue=FakeIssueTrackerService.issue,
        anomalies=anomalies,
        status=alert_group.AlertGroup.Status.triaged,
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    FakeIssueTrackerService.issue.update({
        'state': 'open',
    })
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies + added),
        issue=FakeIssueTrackerService.issue,
    ))

    self.assertEqual(len(group.get().anomalies), 4)
    self.assertEqual(group.get().status,
                     alert_group.AlertGroup.Status.triaged)
    for a in added:
      self.assertIn(a, group.get().anomalies)
      self.assertEqual(group.get().bug.bug_id,
                       FakeIssueTrackerService.add_comment_args[0])
      self.assertIn('Added 2 regressions to the group',
                    FakeIssueTrackerService.add_comment_args[1])

  def testAddAnomalies_GroupTriaged_IssueClosed(self):
    anomalies = [AddAnomaly(), AddAnomaly()]
    added = [AddAnomaly(), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        issue=FakeIssueTrackerService.issue,
        anomalies=anomalies,
        status=alert_group.AlertGroup.Status.closed,
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    FakeIssueTrackerService.issue.update({
        'state': 'closed',
    })
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies + added),
        issue=FakeIssueTrackerService.issue,
    ))

    self.assertEqual(len(group.get().anomalies), 4)
    self.assertEqual('open', FakeIssueTrackerService.issue.get('state'))
    for a in added:
      self.assertIn(a, group.get().anomalies)
      self.assertEqual(group.get().bug.bug_id,
                       FakeIssueTrackerService.add_comment_args[0])
      self.assertIn('Added 2 regressions to the group',
                    FakeIssueTrackerService.add_comment_args[1])

  def testUpdate_GroupTriaged_IssueClosed(self):
    anomalies = [AddAnomaly(), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        issue=FakeIssueTrackerService.issue,
        status=alert_group.AlertGroup.Status.triaged,
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    FakeIssueTrackerService.issue.update({
        'state': 'closed',
    })
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies),
        issue=FakeIssueTrackerService.issue,
    ))

    self.assertEqual(group.get().status, alert_group.AlertGroup.Status.closed)

  def testUpdate_GroupClosed_IssueOpen(self):
    anomalies = [AddAnomaly(), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        issue=FakeIssueTrackerService.issue,
        status=alert_group.AlertGroup.Status.closed,
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    FakeIssueTrackerService.issue.update({
        'state': 'open',
    })
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies),
        issue=FakeIssueTrackerService.issue,
    ))

    self.assertEqual(group.get().status, alert_group.AlertGroup.Status.triaged)

  def testUpdate_GroupTriaged_AlertsAllRecovered(self):
    anomalies = [AddAnomaly(recovered=True), AddAnomaly(recovered=True)]
    group = AddAlertGroup(
        anomalies[0],
        issue=FakeIssueTrackerService.issue,
        status=alert_group.AlertGroup.Status.triaged,
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    FakeIssueTrackerService.issue.update({
        'state': 'open',
    })
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies),
        issue=FakeIssueTrackerService.issue,
    ))

    self.assertEqual('closed', FakeIssueTrackerService.issue.get('state'))

  def testUpdate_GroupTriaged_AlertsPartRecovered(self):
    anomalies = [AddAnomaly(recovered=True), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        issue=FakeIssueTrackerService.issue,
        status=alert_group.AlertGroup.Status.triaged,
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    FakeIssueTrackerService.issue.update({
        'state': 'open',
    })
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies),
        issue=FakeIssueTrackerService.issue,
    ))

    self.assertEqual('open', FakeIssueTrackerService.issue.get('state'))

  def testTriage_GroupUntriaged(self):
    anomalies = [AddAnomaly(), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        status=alert_group.AlertGroup.Status.untriaged,
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
        config=alert_group_workflow.AlertGroupWorkflow.Config(
            active_window=datetime.timedelta(days=7),
            triage_delay=datetime.timedelta(hours=0),
        ),
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies),
        issue=None,
    ))
    self.assertIn('2 regressions', FakeIssueTrackerService.new_bug_args[0])

  def testTriage_GroupUntriaged_InfAnomaly(self):
    anomalies = [AddAnomaly(median_before_anomaly=0), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        status=alert_group.AlertGroup.Status.untriaged,
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
        config=alert_group_workflow.AlertGroupWorkflow.Config(
            active_window=datetime.timedelta(days=7),
            triage_delay=datetime.timedelta(hours=0),
        ),
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies),
        issue=None,
    ))
    self.assertIn('inf', FakeIssueTrackerService.new_bug_args[1])

  def testTriage_GroupTriaged_InfAnomaly(self):
    anomalies = [AddAnomaly(median_before_anomaly=0), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        issue=FakeIssueTrackerService.issue,
        status=alert_group.AlertGroup.Status.triaged,
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies),
        issue=FakeIssueTrackerService.issue,
    ))
    self.assertIn('inf', FakeIssueTrackerService.add_comment_args[1])

  def testArchive_GroupUntriaged(self):
    anomalies = [AddAnomaly(median_before_anomaly=0), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        anomalies=anomalies,
        status=alert_group.AlertGroup.Status.untriaged,
    )
    sheriff = subscription.Subscription(name='sheriff')
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
        config=alert_group_workflow.AlertGroupWorkflow.Config(
            active_window=datetime.timedelta(days=0),
            triage_delay=datetime.timedelta(hours=0),
        ),
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies),
        issue=None,
    ))
    self.assertEqual(False, group.get().active)

  def testArchive_GroupTriaged(self):
    anomalies = [AddAnomaly(median_before_anomaly=0), AddAnomaly()]
    group = AddAlertGroup(
        anomalies[0],
        anomalies=anomalies,
        issue=FakeIssueTrackerService.issue,
        status=alert_group.AlertGroup.Status.triaged,
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    FakeIssueTrackerService.issue.update({
        'state': 'open',
    })
    w = alert_group_workflow.AlertGroupWorkflow(
        group.get(),
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
        config=alert_group_workflow.AlertGroupWorkflow.Config(
            active_window=datetime.timedelta(days=0),
            triage_delay=datetime.timedelta(hours=0),
        ),
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=ndb.get_multi(anomalies),
        issue=FakeIssueTrackerService.issue,
    ))
    self.assertEqual(True, group.get().active)
