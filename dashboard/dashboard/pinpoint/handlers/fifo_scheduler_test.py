# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Tests the FIFO Scheduler Handler."""

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import mock
import unittest
import sys

from dashboard.common import namespaced_stored_object
from dashboard.common import bot_configurations
from dashboard.pinpoint import test
from dashboard.pinpoint.models import job
from dashboard.pinpoint.models import scheduler
from dashboard.pinpoint.models.tasks import bisection_test_util


@mock.patch('dashboard.services.swarming.GetAliveBotsByDimensions',
            mock.MagicMock(return_value=["a"]))
class FifoSchedulerTest(test.TestCase):

  def setUp(self):
    # TODO(https://crbug.com/1262292): Change to super() after Python2 trybots retire.
    # pylint: disable=super-with-arguments
    super(FifoSchedulerTest, self).setUp()
    namespaced_stored_object.Set(bot_configurations.BOT_CONFIGURATIONS_KEY,
                                 {'mock': {}})

  def testSingleQueue(self):
    j = job.Job.New((), (),
                    arguments={'configuration': 'mock'},
                    comparison_mode='performance')
    scheduler.Schedule(j)
    job.Job.Start = mock.MagicMock()

    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)
    self.ExecuteDeferredTasks('default')

    self.assertEqual(job.Job.Start.call_count, 1)

    # Ensure that the job is still running.
    job_id, queue_status = scheduler.PickJobs('mock')[0]
    self.assertEqual(job_id, j.job_id)
    self.assertEqual(queue_status, 'Running')

    # On the next poll, we need to ensure that an ongoing job doesn't get marked
    # completed until it really is completed.
    j.Start = mock.MagicMock()
    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)
    self.ExecuteDeferredTasks('default')
    self.assertFalse(j.Start.called)
    job_id, queue_status = scheduler.PickJobs('mock')[0]
    self.assertEqual(job_id, j.job_id)
    self.assertEqual(queue_status, 'Running')

  def testJobCompletes(self):
    j = job.Job.New((), (),
                    arguments={'configuration': 'mock'},
                    comparison_mode='performance')
    scheduler.Schedule(j)
    job.Job.Start = mock.MagicMock(side_effect=j._Complete)

    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)
    self.ExecuteDeferredTasks('default')

    self.assertEqual(job.Job.Start.call_count, 1)
    job_id, _ = scheduler.PickJobs('mock')[0]
    self.assertIsNone(job_id)

  def testJobFails(self):
    j = job.Job.New((), (),
                    arguments={'configuration': 'mock'},
                    comparison_mode='performance')
    scheduler.Schedule(j)
    job.Job.Start = mock.MagicMock(side_effect=j.Fail)

    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)
    self.ExecuteDeferredTasks('default')

    self.assertEqual(job.Job.Start.call_count, 1)
    job_id, _ = scheduler.PickJobs('mock')[0]
    self.assertIsNone(job_id)

  def testMultipleQueues(self):
    jobs = []
    total_jobs = 2
    total_queues = 10
    for configuration_id in range(total_queues):
      for _ in range(total_jobs):
        j = job.Job.New(
            (), (),
            arguments={'configuration': 'queue-{}'.format(configuration_id)},
            comparison_mode='performance')
        j.Start = mock.MagicMock(side_effect=j._Complete)
        scheduler.Schedule(j)
        jobs.append(j)

    # We ensure that all jobs complete if we poll the fifo-scheduler.
    for _ in range(0, total_jobs):
      response = self.testapp.get('/cron/fifo-scheduler')
      self.assertEqual(response.status_code, 200)
      self.ExecuteDeferredTasks('default')

    # Check for each job that Job.Start() was called.
    for index, j in enumerate(jobs):
      self.assertTrue(j.Start.Called,
                      'job at index {} was not run!'.format(index))

  def testQueueStatsUpdates(self):
    j = job.Job.New((), (),
                    arguments={'configuration': 'mock'},
                    comparison_mode='performance')
    scheduler.Schedule(j)
    job.Job.Start = mock.MagicMock(side_effect=j._Complete)

    # Check that we can find the queued job.
    stats = scheduler.QueueStats('mock')
    self.assertEqual(stats['queued_jobs'], 1)
    self.assertNotIn('running_jobs', stats)
    self.assertEqual(len(stats['queue_time_samples']), 0)

    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)

    self.ExecuteDeferredTasks('default')

    self.assertEqual(job.Job.Start.call_count, 1)
    job_id, _ = scheduler.PickJobs('mock')[0]
    self.assertIsNone(job_id)

    # Check that point-in-time stats are zero, and that we have one sample.
    stats = scheduler.QueueStats('mock')
    self.assertNotIn('queued_jobs', stats)
    self.assertNotIn('running_jobs', stats)
    self.assertNotEqual(len(stats['queue_time_samples']), 0)
    self.assertEqual(len(stats['queue_time_samples'][0]), 2)

  def testJobStuckInRunning(self):
    self.skipTest('Not implemented yet.')

  def testJobCancellationSucceedsOnRunningJob(self):
    j = job.Job.New((), (),
                    arguments={'configuration': 'mock'},
                    comparison_mode='performance')
    scheduler.Schedule(j)
    job.Job.Start = mock.MagicMock()

    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)
    self.ExecuteDeferredTasks('default')

    self.assertEqual(job.Job.Start.call_count, 1)

    # Ensure that the job is still running.
    job_id, queue_status = scheduler.PickJobs('mock')[0]
    self.assertEqual(job_id, j.job_id)
    self.assertEqual(queue_status, 'Running')

    # We can cancel a running job.
    self.assertTrue(scheduler.Cancel(j))

    # Ensure that the job is still running.
    job_id, queue_status = scheduler.PickJobs('mock')[0]
    self.assertNotEqual(job_id, j.job_id)
    self.assertNotEqual(queue_status, 'Running')

  def testJobCancellationSucceedsOnQueuedJob(self):
    j = job.Job.New((), (),
                    arguments={'configuration': 'mock'},
                    comparison_mode='performance')
    scheduler.Schedule(j)
    j.Start = mock.MagicMock()
    self.assertTrue(scheduler.Cancel(j))

    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)
    self.ExecuteDeferredTasks('default')
    self.assertFalse(j.Start.called)

  def testJobSamplesCapped(self):
    for _ in range(51):
      j = job.Job.New((), (),
                      arguments={'configuration': 'mock'},
                      comparison_mode='performance')
      scheduler.Schedule(j)
      j.Start = mock.MagicMock(side_effect=j._Complete)
      response = self.testapp.get('/cron/fifo-scheduler')
      self.assertEqual(response.status_code, 200)

    self.ExecuteDeferredTasks('default')

    stats = scheduler.QueueStats('mock')
    self.assertLessEqual(len(stats.get('queue_time_samples')), 50)

  def testSchedulePriorityOrder(self):
    j0 = job.Job.New((), (),
                     arguments={'configuration': 'mock'},
                     comparison_mode='performance')
    scheduler.Schedule(j0)

    j1 = job.Job.New((), (),
                     arguments={
                         'configuration': 'mock',
                         'priority': '100',
                     },
                     comparison_mode='performance',
                     priority=100)
    scheduler.Schedule(j1)

    j2 = job.Job.New((), (),
                     arguments={'configuration': 'mock'},
                     comparison_mode='performance')
    scheduler.Schedule(j2)

    # The first time we call the scheduler, it must mark j0 completed.
    job.Job.Start = mock.MagicMock(side_effect=j0._Complete)
    self.assertEqual(
        scheduler.QueueStats('mock')['job_id_with_status'][0]['job_id'], '1')
    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)
    self.ExecuteDeferredTasks('default')
    self.assertEqual(job.Job.Start.call_count, 1)

    # Next time, j2 should be completed.
    job.Job.Start.side_effect = j2._Complete
    self.assertEqual(
        scheduler.QueueStats('mock')['job_id_with_status'][0]['job_id'], '3')
    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)
    self.ExecuteDeferredTasks('default')
    self.assertEqual(job.Job.Start.call_count, 2)

    # Then we should have j1 completed.
    job.Job.Start.side_effect = j1._Complete
    self.assertEqual(
        scheduler.QueueStats('mock')['job_id_with_status'][0]['job_id'], '2')
    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)
    self.ExecuteDeferredTasks('default')
    self.assertEqual(job.Job.Start.call_count, 3)


# TODO(dberris): Need to mock *all* of the back-end services that the various
# "live" bisection operations will be looking into.
@mock.patch('dashboard.services.swarming.GetAliveBotsByDimensions',
            mock.MagicMock(return_value=["a"]))
@unittest.skipIf(sys.version_info.major == 3,
                 'Skipping as execution Engine setup not ready for python 3.')
class FifoSchedulerExecutionEngineTest(bisection_test_util.BisectionTestBase):

  def setUp(self):
    # TODO(https://crbug.com/1262292): Change to super() after Python2 trybots retire.
    # pylint: disable=super-with-arguments
    super(FifoSchedulerExecutionEngineTest, self).setUp()
    namespaced_stored_object.Set(bot_configurations.BOT_CONFIGURATIONS_KEY,
                                 {'mock': {}})

  def testJobRunInExecutionEngine(self):
    j = job.Job.New((), (),
                    arguments={'configuration': 'mock'},
                    comparison_mode='performance',
                    use_execution_engine=True)
    self.PopulateSimpleBisectionGraph(j)
    scheduler.Schedule(j)
    j.Start = mock.MagicMock(side_effect=j._Complete)

    response = self.testapp.get('/cron/fifo-scheduler')
    self.assertEqual(response.status_code, 200)
    self.ExecuteDeferredTasks('default')

    self.assertTrue(j.Start.called)
    job_id, _ = scheduler.PickJobs('mock')[0]
    self.assertIsNone(job_id)


@mock.patch('dashboard.services.swarming.GetAliveBotsByDimensions',
            mock.MagicMock(return_value=["a"]))
class FifoSchedulerCostModelTest(test.TestCase):

  def setUp(self):
    # TODO(https://crbug.com/1262292): Change to super() after Python2 trybots retire.
    # pylint: disable=super-with-arguments
    super(FifoSchedulerCostModelTest, self).setUp()
    # We're setting up a cost model where tryjobs cost half as much as a
    # performance or functional bisection, and ensure that we're seeing the
    # budget consumed appropriately in a scheduling iteration.
    namespaced_stored_object.Set(
        bot_configurations.BOT_CONFIGURATIONS_KEY, {
            'mock': {
                'scheduler': {
                    'cost': {
                        'try': 0.5,
                        'performance': 1.0,
                        'functional': 1.0
                    },
                    'budget': 2.0
                }
            }
        })

  def testSchedule_AllBisections(self):

    def CreateAndSchedule():
      j = job.Job.New((), (),
                      arguments={'configuration': 'mock'},
                      comparison_mode='performance')
      scheduler.Schedule(j)
      return j

    jobs = [CreateAndSchedule() for _ in range(10)]

    def CompleteJobAndPop():
      jobs[0]._Complete()
      jobs.pop(0)

    job.Job.Start = mock.MagicMock(side_effect=CompleteJobAndPop)

    # We want to ensure that every iteration, we'll have two of the bisections
    # started, given our cost model and budget.
    for offset in range(1, 5):
      response = self.testapp.get('/cron/fifo-scheduler')
      self.assertEqual(response.status_code, 200)
      self.ExecuteDeferredTasks('default')
      self.assertEqual(job.Job.Start.call_count, offset * 2)
      self.assertEqual(
          scheduler.QueueStats('mock')['job_id_with_status'][0]['job_id'],
          str(offset * 2 + 1))
      self.assertEqual(
          scheduler.QueueStats('mock')['queued_jobs'], 10 - offset * 2)
