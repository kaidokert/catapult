# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import mock
import unittest
import webapp2
import webtest

from dashboard import update_dashboard_stats
from dashboard.pinpoint.models.change import change
from dashboard.pinpoint.models.change import commit
from dashboard.pinpoint.models import job as job_module
from dashboard.pinpoint.models import job_state
from dashboard.pinpoint.models.quest import execution_test
from dashboard.pinpoint.models.quest import quest
from dashboard.pinpoint import test


_RESULTS_BY_CHANGE = {
    'chromium@aaaaaaa': [1, 1, 1, 1],
    'chromium@bbbbbbb': [5, 5, 5, 5]
}

class _QuestStub(quest.Quest):

  def __str__(self):
    return 'Quest'

  def Start(self, c):
    return ExecutionResults(c)

  @classmethod
  def FromDict(cls, arguments):
    return cls


class ExecutionResults(execution_test._ExecutionStub):
  def __init__(self, c):
    super(ExecutionResults, self).__init__()
    self._result_for_test = _RESULTS_BY_CHANGE[str(c)]

  def _Poll(self):
    self._Complete(result_arguments={'arg key': 'arg value'},
                   result_values=self._result_for_test)


class UpdateDashboardStatsTest(test.TestCase):

  def setUp(self):
    super(UpdateDashboardStatsTest, self).setUp()
    app = webapp2.WSGIApplication(
        [('/update_dashboard_stats',
          update_dashboard_stats.UpdateDashboardStatsHandler)])
    self.testapp = webtest.TestApp(app)

  def _CreateJob(
      self, hash1, hash2, comparison_mode, created, bug_id, exception=None):
    old_commit = commit.Commit('chromium', hash1)
    change_a = change.Change((old_commit,))

    old_commit = commit.Commit('chromium', hash2)
    change_b = change.Change((old_commit,))

    job = job_module.Job.New(
        (_QuestStub(),), (change_a, change_b),
        comparison_mode=comparison_mode,
        bug_id=bug_id)
    job.created = created
    job.exception = exception
    job.state.ScheduleWork()
    job.state.Explore()
    job.put()

  @mock.patch.object(
      change.Change, 'Midpoint',
      mock.MagicMock(side_effect=commit.NonLinearError))
  @mock.patch.object(
      update_dashboard_stats.deferred, 'defer')
  def testPost_Success(self, mock_defer):
    created = datetime.datetime.now() - datetime.timedelta(days=1)
    self._CreateJob(
        'aaaaaaaa', 'bbbbbbbb', job_state.PERFORMANCE, created, 12345)

    self.testapp.post('/update_dashboard_stats')
    self.assertTrue(mock_defer.called)

  @mock.patch.object(
      change.Change, 'Midpoint',
      mock.MagicMock(side_effect=commit.NonLinearError))
  @mock.patch.object(
      update_dashboard_stats.deferred, 'defer')
  def testPost_NoResults(self, mock_defer):
    created = datetime.datetime.now() - datetime.timedelta(days=1)
    self._CreateJob(
        'aaaaaaaa', 'bbbbbbbb', job_state.FUNCTIONAL, created, 12345)

    created = datetime.datetime.now() - datetime.timedelta(days=15)
    self._CreateJob(
        'aaaaaaaa', 'bbbbbbbb', job_state.PERFORMANCE, created, 12345)

    created = datetime.datetime.now() - datetime.timedelta(days=1)
    self._CreateJob(
        'aaaaaaaa', 'bbbbbbbb', job_state.PERFORMANCE, created, None)

    created = datetime.datetime.now() - datetime.timedelta(days=1)
    self._CreateJob(
        'aaaaaaaa', 'aaaaaaaa', job_state.PERFORMANCE, created, 12345)

    created = datetime.datetime.now() - datetime.timedelta(days=1)
    self._CreateJob(
        'aaaaaaaa', 'bbbbbbbb', job_state.PERFORMANCE, created, 12345, 'foo')

    self.testapp.post('/update_dashboard_stats')
    self.assertFalse(mock_defer.called)


if __name__ == '__main__':
  unittest.main()
