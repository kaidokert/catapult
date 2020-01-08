# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest
import psutil  # pylint: disable=import-error
from telemetry import decorators
from telemetry.internal.util import ps_util


class PsUtilTest(unittest.TestCase):

  @decorators.Disabled('chromeos')  # crbug.com/939730
  def testListAllSubprocesses_RaceCondition(self):
    """This is to check that crbug.com/934575 stays fixed."""
    class FakeProcess(object):
      def __init__(self):
        self.pid = '1234'
      def name(self):
        raise psutil.ZombieProcess('this is an error')
    output = ps_util._GetProcessDescription(FakeProcess())
    self.assertIn('ZombieProcess', output)
    self.assertIn('this is an error', output)

  def testWaitForSubProcAndKillFinished(self):
    args = [
        'python',
        '-c',
        'import time; time.sleep(2)'
    ]
    sp = ps_util.RunSubProcWithTimeout(args, 3)
    self.assertEqual(sp.returncode, 0)
    self.assertTrue(
        sp.pid not in ps_util.GetAllSubprocesses()
    )

  def testWaitForSubProcAndKillTimeout(self):
    args = [
        'python',
        '-c',
        'import time; time.sleep(2)'
    ]
    sp = ps_util.RunSubProcWithTimeout(args, 3)
    self.assertEqual(sp.returncode, None)
    self.assertTrue(
        sp.pid in ps_util.GetAllSubprocesses()
    )
