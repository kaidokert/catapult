# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import itertools
import unittest

from dashboard.pinpoint.models.quest import execution_test
from dashboard.pinpoint.models.quest import quest


class _QuestStub(quest.Quest):

  def __str__(self):
    return 'Quest'

  @classmethod
  def FromDict(cls, arguments):
    return cls()


class QuestCycle(_QuestStub):
  """Cycles through the given execution classes."""

  def __init__(self, *execution_classes):
    self._execution_classes = itertools.cycle(execution_classes)

  def Start(self, change):
    del change
    return self._execution_classes.next()()


class QuestByChange(_QuestStub):
  """Uses a different Execution for each Change."""

  def __init__(self, change_mapping):
    self._change_mapping = change_mapping

  def Start(self, change):
    return self._change_mapping[change]()


class QuestException(_QuestStub):

  def Start(self, change):
    del change
    return execution_test.ExecutionException()


class QuestFail(_QuestStub):

  def Start(self, change):
    del change
    return execution_test.ExecutionFail()


class QuestPass(_QuestStub):

  def Start(self, change):
    del change
    return execution_test.ExecutionPass()


class QuestSpin(_QuestStub):

  def Start(self, change):
    del change
    return execution_test.ExecutionSpin()


class QuestTest(unittest.TestCase):

  def testQuest(self):
    with self.assertRaises(NotImplementedError):
      str(quest.Quest())

    with self.assertRaises(AttributeError):
      quest.Quest().Start()

    with self.assertRaises(NotImplementedError):
      quest.Quest.FromDict({})
