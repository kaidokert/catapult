# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import shutil
import tempfile
import unittest

import long_term_health


class TestMilestoneInfo(unittest.TestCase):
  pass


class TestGetChromiumLog(unittest.TestCase):
  pass


class TestGetBranchInfo(unittest.TestCase):
  pass


class TestGenerateFullInfoCSV(unittest.TestCase):
  pass


class TestDownloadAPKFromURI(unittest.TestCase):
  pass


class TestGetLocalAPK(unittest.TestCase):

  def setUp(self):
    self.test_dir = tempfile.mkdtemp()

  def tearDown(self):
    shutil.rmtree(self.test_dir)

  def testGetLocalAPKNoLocal(self):
    self.assertIsNone(long_term_health.GetLocalAPK(64, self.test_dir))

  def testGetLocalAPKHaveLocal(self):
    file_name = '48.0.2564.116_arm_ChromeStable.apk'
    with open(os.path.join(self.test_dir, file_name), 'wb') as tmp_file:
      tmp_file.write('this is an apk')
    self.assertIsNone(long_term_health.GetLocalAPK(
        48, os.path.join(self.test_dir, file_name)))


class TestGetAPK(unittest.TestCase):
  pass


class TestDecrementPatchNumber(unittest.TestCase):

  def testDecrementPatchNumberNormalUsage(self):
    decremented_patch = long_term_health.DecrementPatchNumber('68.0.3440.70', 6)
    self.assertEqual(decremented_patch, '68.0.3440.64')


class TestBuildArgumentParser(unittest.TestCase):
  pass


class TestProcessArguments(unittest.TestCase):
  class NameSpace(object):

    def __init__(self, from_milestone, to_milestone, from_date, to_date):
      self.from_milestone = from_milestone
      self.to_milestone = to_milestone
      self.from_date = from_date
      self.to_date = to_date

  def testProcessArgument(self):
    pass

  def testProcessArgumentFromMilestone(self):
    pass

  def testProcessArgumentFromMilestoneToMilestone(self):
    args = TestProcessArguments.NameSpace(54, 60, None, None)
    long_term_health.ProcessArguments(args, None)
    self.assertEqual(args.from_milestone, 54)
    self.assertEqual(args.to_milestone, 60)
    self.assertIsNone(args.from_date)
    self.assertIsNone(args.to_date)

  def testProcessArgumentFromDate(self):
    pass

  def testProcessArgumentFromDateToDate(self):
    pass


# do I need to test the main function as well?
if __name__ == '__main__':
  unittest.main()
