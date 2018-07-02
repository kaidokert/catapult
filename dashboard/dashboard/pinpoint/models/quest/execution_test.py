# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from dashboard.pinpoint.models.quest import execution
from dashboard.pinpoint.models.quest import execution_stub


class ExecutionTest(unittest.TestCase):

  def testExecution(self):
    e = execution.Execution()

    self.assertFalse(e.completed)
    self.assertFalse(e.failed)
    self.assertIsNone(e.exception)
    self.assertEqual(e.result_values, ())
    self.assertEqual(e.result_arguments, {})

    with self.assertRaises(NotImplementedError):
      e.AsDict()
    with self.assertRaises(NotImplementedError):
      e.Poll()

  def testExecutionCompleted(self):
    e = execution_stub.ExecutionPass()
    e.Poll()

    with self.assertRaises(AssertionError):
      e.Poll()

    self.assertTrue(e.completed)
    self.assertFalse(e.failed)
    self.assertIsNone(e.exception)
    self.assertEqual(e.result_values, (1, 2, 3))
    self.assertEqual(e.result_arguments, {'arg key': 'arg value'})
    expected = {
        'completed': True,
        'exception': None,
        'details': {'details key': 'details value'},
    }
    self.assertEqual(e.AsDict(), expected)

  def testExecutionException(self):
    e = execution_stub.ExecutionException()
    with self.assertRaises(StandardError):
      e.Poll()

  def testExecutionFailed(self):
    e = execution_stub.ExecutionFail()
    e.Poll()

    self.assertTrue(e.completed)
    self.assertTrue(e.failed)
    expected = 'Exception: Expected error for testing.'
    self.assertEqual(e.exception.splitlines()[-1], expected)
    self.assertEqual(e.result_values, ())
    self.assertEqual(e.result_arguments, {})
