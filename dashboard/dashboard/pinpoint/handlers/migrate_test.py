# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

import mock

from dashboard.pinpoint.handlers import migrate
from dashboard.pinpoint.models import job
from dashboard.pinpoint.models import job_state
from dashboard.pinpoint import test


class MigrateTest(test.TestCase):

  def setUp(self):
    super(MigrateTest, self).setUp()

    patcher = mock.patch.object(migrate, 'datetime', _DatetimeStub())
    self.addCleanup(patcher.stop)
    patcher.start()

    for _ in xrange(20):
      job.Job.New((), ())

  def testNoMigration(self):
    response = self.testapp.get('/api/migrate', status=200)
    self.assertEqual(response.normal_body, '{}')

  def testStart(self):
    expected = json.dumps({
        'count': 0,
        'started': 'Date Time',
        'total': 20,
    })

    response = self.testapp.post('/api/migrate', status=200)
    self.assertEqual(response.normal_body, expected)

    response = self.testapp.get('/api/migrate', status=200)
    self.assertEqual(response.normal_body, expected)

    tasks = self.GetTaskQueueTasks('default')
    self.assertEqual(len(tasks), 1)

    task = tasks.pop()
    self.assertEqual(task['url'], '/api/migrate')
    self.assertEqual(task['method'], 'POST')
    self.assertFalse(task['body'])

  def testContinue(self):
    expected = json.dumps({
        'count': 10,
        'started': 'Date Time',
        'total': 20,
    })

    self.testapp.post('/api/migrate', status=200)

    task_responses = self.ExecuteTaskQueueTasks('/api/migrate', 'default')
    self.assertEqual(task_responses[0].normal_body, expected)
    self.assertEqual(task_responses[1].normal_body, '{}')

    self.assertEqual(len(task_responses), 2)

  def testComplete(self):
    self.testapp.post('/api/migrate', status=200)
    task_responses = self.ExecuteTaskQueueTasks('/api/migrate', 'default')
    self.assertEqual(task_responses[-1].normal_body, '{}')

    response = self.testapp.get('/api/migrate', status=200)
    self.assertEqual(response.normal_body, '{}')

    self.assertEqual(len(task_responses), 2)

  def testJobsMigrated(self):
    job_state.JobState.__setstate__ = _JobStateSetState

    self.testapp.post('/api/migrate', status=200)
    self.ExecuteTaskQueueTasks('/api/migrate', 'default')

    del job_state.JobState.__setstate__

    jobs = job.Job.query().fetch()
    for j in jobs:
      self.assertEqual(j.state._new_field, 'new value')


def _JobStateSetState(self, state):
  self.__dict__ = state
  self._new_field = 'new value'


class _DatetimeStub(object):

  # pylint: disable=invalid-name
  class datetime(object):

    def isoformat(self):
      return 'Date Time'

    @classmethod
    def now(cls):
      return cls()
