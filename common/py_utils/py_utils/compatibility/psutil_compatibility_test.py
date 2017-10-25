#!/usr/bin/env python
# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import multiprocessing
import os
import psutil
import sys
import unittest


class PSUtilCompatibilityTest(unittest.TestCase):
  """Compatibility tests for psutil methods used in catapult.

  Tests known to pass in psutil: 2.0.0, 2.2.1, and 5.4.0.

  Tests known to fail in psutil: 0.x and 1.x.
  """

  def setUp(self):
    self.current_pid = os.getpid()

  def testGetProperties(self):
    """Test that process methods return values of expected types."""
    p = psutil.Process(self.current_pid)
    self.assertEqual(p.pid, self.current_pid)
    self.assertIsInstance(p.name(), str)
    self.assertIsInstance(p.create_time(), float)

    cmdline = p.cmdline()
    self.assertIsInstance(cmdline, list)
    self.assertTrue(
        all(isinstance(arg, str) for arg in cmdline),
        '%r is not a list of str' % cmdline)

  def testProcessIter(self):
    """Test that we can find ourselves in the running processes."""
    self.assertTrue(
        any(p.pid == self.current_pid for p in psutil.process_iter()))

  def testGetChildren(self):
    """Test that we can find our own subprocesses."""
    def NoOp():
      pass

    q = multiprocessing.Process(target=NoOp)
    q.start()
    children = psutil.Process(self.current_pid).children(recursive=True)
    self.assertEqual(len(children), 1)
    self.assertEqual(children[0].pid, q.pid)
    q.join()

  def testCpuAffinity(self):
    """Test that we can set and reset cpu affinity."""
    p = psutil.Process(self.current_pid)
    old_affinity = p.cpu_affinity()  # Save original affinity.
    try:
      p.cpu_affinity([0])  # Set new affinity.
      self.assertEqual(p.cpu_affinity(), [0])
    finally:
      p.cpu_affinity(old_affinity)  # Restore original affinity.


if __name__ == '__main__':
  sys.exit(unittest.main())
