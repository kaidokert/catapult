# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import mock
import datetime

from dashboard.common import testing_common
from dashboard.common import utils
from dashboard.models import alert_group
from dashboard.models import anomaly
from dashboard.models import graph_data
from dashboard.models import subscription
from dashboard.services import crrev_service
from dashboard.services import pinpoint_service

from dashboard import sheriff_config_client

class MockIssueTrackerService(object):
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

  issue = {
      'cc': [
          {
              'kind': 'monorail#issuePerson',
              'htmlLink': 'https://bugs.chromium.org/u/1253971105',
              'name': 'user@chromium.org',
          }, {
              'kind': 'monorail#issuePerson',
              'name': 'hello@world.org',
          }
      ],
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
      'state': 'open',
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


class AlertGroupTest(testing_common.TestCase):

  def setUp(self):
    super(AlertGroupTest, self).setUp()
    self.maxDiff = None

  def _AddAnomaly(self, **kargs):
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
    graph_data.TestMetadata(key=default['test']).put()
    a = anomaly.Anomaly(**default)
    a.groups = alert_group.AlertGroup.GetGroupsForAnomaly(a)
    return a.put()

  def testTryBisect(self):
    alert_key = self._AddAnomaly()
    group_key = alert_group.AlertGroup.GenerateAllGroupsForAnomaly(
        alert_key.get())[0].put()
    alert = alert_key.get()
    alert.groups = [group_key]
    alert.put()

    sheriff = subscription.Subscription(
        name='sheriff', auto_triage_enable=True, auto_bisect_enable=True)
    mock_sheriff_config_client = mock.MagicMock()
    mock_sheriff_config_client.Match = mock.MagicMock(
        return_value=([sheriff], None))
    self.PatchObject(sheriff_config_client, 'GetSheriffConfigClient',
                     lambda: mock_sheriff_config_client)
    self.PatchObject(alert_group, '_IssueTracker',
                     lambda: MockIssueTrackerService)
    self.PatchObject(utils, 'GetServiceAccountCredential',
                     lambda: {'client_email': 'test@g.com', 'private_key': ''})
    self.PatchObject(crrev_service, 'GetNumbering',
                     lambda *args, **kargs: {'git_sha': 'abcd'})
    self.PatchObject(pinpoint_service, 'NewJob',
                     mock.MagicMock(return_value={'jobId': '123456'}))

    # Auto-Bisection require AlertGroup triaged
    group = group_key.get()
    group.status = alert_group.AlertGroup.Status.triaged
    group.bug = alert_group.BugInfo(project='chromium', bug_id=12345)
    group.put()

    # Trigger auto-bisection
    group = group_key.get()
    group.Update(
        datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        datetime.timedelta(hours=0),
        datetime.timedelta(hours=0),
    )
    self.assertIsNotNone(pinpoint_service.NewJob.call_args)
    self.assertItemsEqual(group_key.get().bisection_ids, ['123456'])
