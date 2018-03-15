# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import webapp2
import webtest

from dashboard.common import testing_common
from dashboard.pinpoint.handlers import monitor
from dashboard.pinpoint.models import job as job_module


class MonitorTest(testing_common.TestCase):

  def setUp(self):
    super(MonitorTest, self).setUp()

    app = webapp2.WSGIApplication([
        webapp2.Route(r'/api/monitor', monitor.Monitor),
    ])
    self.testapp = webtest.TestApp(app)

  def testCompletedJob(self):
    job = job_module.Job.New({}, [], False)
    job.put()

    self.testapp.post('/api/monitor', status=200)
    self.assertIsNone(job.task)

  def testFreshJob(self):
    job = job_module.Job.New({}, [], False)
    job.task = 'task'
    job.put()

    self.testapp.post('/api/monitor', status=200)
    self.assertEqual(job.task, 'task')

  def testStaleJob(self):
    job = job_module.Job.New({}, [], False)
    job.task = 'task'
    job.updated = datetime.datetime.now() - datetime.timedelta(minutes=11)
    job.put()

    self.testapp.post('/api/monitor', status=200)
    self.assertNotEqual(job.task, 'task')
