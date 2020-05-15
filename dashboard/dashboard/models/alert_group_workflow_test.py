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


class AlertGroupWorkflowTest(testing_common.TestCase):

  def setUp(self):
    super(AlertGroupWorkflowTest, self).setUp()
    self.maxDiff = None

  def testUpdateUntriagedAnomalies(self):
    a = AddAnomaly()
    group = alert_group.AlertGroup.GenerateAllGroupsForAnomaly(a.get())[0]
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    w = alert_group_workflow.AlertGroupWorkflow(
        group,
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=[a.get()],
        issue={},
    ))

  def testUpdateTriagedAnomalies(self):
    a = AddAnomaly()
    group = alert_group.AlertGroup.GenerateAllGroupsForAnomaly(a.get())[0]
    group.bug = alert_group.BugInfo(
        bug_id=FakeIssueTrackerService.issue.get('id'),
        project=FakeIssueTrackerService.issue.get('chromium'),
    )
    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True)
    w = alert_group_workflow.AlertGroupWorkflow(
        group,
        sheriff_config=FakeSheriffConfigClient({
            'master/bot/test_suite/measurement/test_case': [sheriff],
        }),
        issue_tracker=FakeIssueTrackerService,
    )
    w.Process(update=alert_group_workflow.AlertGroupWorkflow.GroupUpdate(
        now=datetime.datetime.utcnow(),
        anomalies=[a.get()],
        issue=FakeIssueTrackerService.issue,
    ))
