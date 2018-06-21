# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import itertools
import unittest

from dashboard.pinpoint.models import job_state
from dashboard.pinpoint.models import quest


class ExploreTest(unittest.TestCase):

  def testDifferent(self):
    # TODO(dtu): Implement when we have more powerful mocking available.
    pass

  def testPending(self):
    state = job_state.JobState([_QuestStub(_ExecutionPass)],
                               comparison_mode=job_state.PERFORMANCE)
    state.AddChange('change 1')
    state.AddChange('change 2')

    state.Explore()

    self.assertEqual(len(state._changes), 2)
    self.assertEqual(len(state._attempts['change 1']), 10)
    self.assertEqual(len(state._attempts['change 2']), 10)

  def testSame(self):
    state = job_state.JobState([_QuestStub(_ExecutionPass)],
                               comparison_mode=job_state.PERFORMANCE)
    state.AddChange('change 1')
    state.AddChange('change 2')

    state.ScheduleWork()
    state.Explore()

    self.assertEqual(len(state._changes), 2)
    self.assertEqual(len(state._attempts['change 1']), 10)
    self.assertEqual(len(state._attempts['change 2']), 10)

  def testUnknown(self):
    state = job_state.JobState([_QuestStub(_ExecutionPass)],
                               comparison_mode=job_state.FUNCTIONAL)
    state.AddChange('change 1')
    state.AddChange('change 2')

    state.ScheduleWork()
    state.Explore()

    self.assertEqual(len(state._attempts['change 1']), 20)
    self.assertEqual(len(state._attempts['change 2']), 10)

    state.ScheduleWork()
    state.Explore()

    self.assertEqual(len(state._attempts['change 1']), 20)
    self.assertEqual(len(state._attempts['change 2']), 20)


class ScheduleWorkTest(unittest.TestCase):

  def testNoAttempts(self):
    state = job_state.JobState(())
    self.assertFalse(state.ScheduleWork())

  def testWorkLeft(self):
    state = job_state.JobState([_QuestStub(_ExecutionPass, _ExecutionSpin)])
    state.AddChange('change')
    self.assertTrue(state.ScheduleWork())

  def testNoWorkLeft(self):
    state = job_state.JobState([_QuestStub(_ExecutionPass)])
    state.AddChange('change')
    self.assertTrue(state.ScheduleWork())
    self.assertFalse(state.ScheduleWork())

  def testAllAttemptsFail(self):
    q = _QuestStub(_ExecutionFail, _ExecutionFail, _ExecutionFail2)
    state = job_state.JobState([q])
    state.AddChange('change')
    expected_regexp = '7/10.*\nException: Expected error for testing.$'
    self.assertTrue(state.ScheduleWork())
    with self.assertRaisesRegexp(Exception, expected_regexp):
      self.assertFalse(state.ScheduleWork())


class _QuestStub(quest.Quest):

  def __init__(self, *execution_classes):
    self._execution_classes = itertools.cycle(execution_classes)

  def __str__(self):
    return 'Quest'

  def Start(self, change):
    del change
    return self._execution_classes.next()()

  @classmethod
  def FromDict(cls, arguments):
    return cls


class _ExecutionFail(quest.Execution):
  """This Execution always fails on first Poll()."""

  def _Poll(self):
    raise Exception('Expected error for testing.')

  def _AsDict(self):
    return {}


class _ExecutionFail2(quest.Execution):
  """This Execution always fails on first Poll()."""

  def _Poll(self):
    raise Exception('A different expected error for testing.')

  def _AsDict(self):
    return {}


class _ExecutionPass(quest.Execution):
  """This Execution always completes on first Poll()."""

  def _Poll(self):
    self._Complete()

  def _AsDict(self):
    return {}


class _ExecutionSpin(quest.Execution):
  """This Execution never completes."""

  def _Poll(self):
    pass

  def _AsDict(self):
    return {}
