# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import logging
import mock
import sys
import unittest

from dashboard.pinpoint.models import exploration


def FindMidpoint(a, b):
  if a == b or b - a == 1:
    return None
  offset = (b - a) // 2
  if offset == 0:
    offset += 1
  return a + offset


class ExplorationTest(unittest.TestCase):

  def setUp(self):
    # Intercept the logging messages, so that we can see them when we have test
    # output in failures.
    self.logger = logging.getLogger()
    self.logger.level = logging.DEBUG
    self.stream_handler = logging.StreamHandler(sys.stdout)
    self.logger.addHandler(self.stream_handler)
    self.addCleanup(self.logger.removeHandler, self.stream_handler)

  def testSpeculateEmpty(self):
    ChangeDetected = mock.MagicMock(  # pylint: disable=invalid-name
        return_value=False)
    OnUnknown = mock.MagicMock()  # pylint: disable=invalid-name
    FakeFindMidpoint = mock.MagicMock() # pylint: disable=invalid-name
    results = exploration.Speculate([],
                                    change_detected=ChangeDetected,
                                    on_unknown=OnUnknown,
                                    midpoint=FakeFindMidpoint,
                                    levels=100)
    self.assertEqual(results, [])
    self.assertFalse(ChangeDetected.called)
    self.assertFalse(OnUnknown.called)
    self.assertFalse(FakeFindMidpoint.called)

  def testSpeculateOdd(self):
    OnUnknown = mock.MagicMock()  # pylint: disable=invalid-name
    changes = [1, 9]

    def ChangeDetected(*_):
      return True

    results = exploration.Speculate(
        changes,
        change_detected=ChangeDetected,
        on_unknown=OnUnknown,
        midpoint=FindMidpoint,
        levels=2)
    for index, change in results:
      changes.insert(index, change)
    self.assertFalse(OnUnknown.called)
    self.assertEqual(changes, [1, 3, 5, 7, 9])

  def testSpeculateEven(self):
    OnUnknown = mock.MagicMock()  # pylint: disable=invalid-name
    changes = [0, 100]

    def ChangeDetected(*_):
      return True

    results = exploration.Speculate(
        changes,
        change_detected=ChangeDetected,
        on_unknown=OnUnknown,
        midpoint=FindMidpoint,
        levels=2)
    for index, change in results:
      changes.insert(index, change)
    self.assertFalse(OnUnknown.called)
    self.assertEqual(changes, [0, 25, 50, 75, 100])

  def testSpeculateUnbalanced(self):
    OnUnknown = mock.MagicMock()  # pylint: disable=invalid-name
    changes = [0, 9, 100]

    def ChangeDetected(*_):
      return True

    results = exploration.Speculate(
        changes,
        change_detected=ChangeDetected,
        on_unknown=OnUnknown,
        midpoint=FindMidpoint,
        levels=2)
    for index, change in results:
      changes.insert(index, change)
    self.assertFalse(OnUnknown.called)
    self.assertEqual(changes, [0, 2, 4, 6, 9, 31, 54, 77, 100])

  def testSpeculateIterations(self):
    OnUnknown = mock.MagicMock()  # pylint: disable=invalid-name
    changes = [0, 10]

    def ChangeDetected(*_):
      return True

    results = exploration.Speculate(
        changes,
        change_detected=ChangeDetected,
        on_unknown=OnUnknown,
        midpoint=FindMidpoint,
        levels=2)
    for index, change in results:
      changes.insert(index, change)
    self.assertFalse(OnUnknown.called)
    self.assertEqual(changes, [0, 2, 5, 7, 10])

    # Run the bisection again and get the full range.
    OnUnknown = mock.MagicMock()  # pylint: disable=invalid-name
    results = exploration.Speculate(
        changes,
        change_detected=ChangeDetected,
        on_unknown=OnUnknown,
        midpoint=FindMidpoint,
        levels=2)
    for index, change in results:
      changes.insert(index, change)
    self.assertFalse(OnUnknown.called)
    self.assertEqual(changes, range(11))

  def testSpeculateHandleUnknown(self):
    OnUnknown = mock.MagicMock()  # pylint: disable=invalid-name
    changes = [0, 10]

    def ChangeDetected(*_):
      return None

    results = exploration.Speculate(
        changes,
        change_detected=ChangeDetected,
        on_unknown=OnUnknown,
        midpoint=FindMidpoint,
        levels=2)
    for index, change in results:
      changes.insert(index, change)
    self.assertTrue(OnUnknown.called)
    self.assertEqual(changes, [0, 10])
