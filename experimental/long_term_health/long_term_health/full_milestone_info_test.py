# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import csv
import os
import tempfile
from unittest import TestCase

from long_term_health import full_milestone_info
from long_term_health import utils
import mock


class TestGetBranchInfo(TestCase):

  @mock.patch('long_term_health.full_milestone_info.GetChromiumLog')
  def testGetBranchInfo(self, get_chromium_log_function):
    # this is an incomplete log result, some attributes are omitted
    get_chromium_log_function.return_value = [{
        'committer': {
            'name': 'chrome-release-bot@chromium.org',
            'email': 'chrome-release-bot@chromium.org',
            'time': 'Fri Apr 13 00:33:52 2018'
        },
        'message': 'Incrementing VERSION to 65.0.3325.230'
    }]
    milestone, branch, version_num, release_date = (
        full_milestone_info.GetBranchInfo('65', '3325'))
    self.assertEqual('65', milestone)
    self.assertEqual('3325', branch)
    self.assertEqual('65.0.3325.230', version_num)
    self.assertEqual('2018-04-13T00:33:52', release_date)


class TestMilestoneInfo(TestCase):

  def setUp(self):
    _, self.csv_path = tempfile.mkstemp('.csv')
    with open(self.csv_path, 'w') as tmp_csv:
      fieldnames = ['milestone', 'branch', 'version_number', 'release_date']
      writer = csv.DictWriter(tmp_csv, fieldnames=fieldnames)
      writer.writeheader()
      # fake data row
      writer.writerow(
          {
              'milestone': 13,
              'branch': 234,
              'version_number': '13.0.0.250',
              'release_date': '2013-07-20T00:39:24'
          }
      )
      # real data row
      writer.writerow(
          {
              'milestone': 62,
              'branch': 3202,
              'version_number': '62.0.3202.101',
              'release_date': '2017-11-17T01:03:27'
          }
      )
      # fake data row
      writer.writerow(
          {
              'milestone': 103,
              'branch': 2304,
              'version_number': '103.0.0.250',
              'release_date': '2103-07-20T00:39:24'
          }
      )
    self.milestone_info = full_milestone_info.MilestoneInfo(self.csv_path)

  def tearDown(self):
    os.remove(self.csv_path)

  def testInit(self):
    milestones = self.milestone_info
    self.assertEqual(13, milestones._table[0]['milestone'])
    self.assertEqual(234, milestones._table[0]['branch'])
    self.assertEqual('13.0.0.250', milestones._table[0]['version_number'])
    self.assertEqual(utils.ParseIsoFormatDate('2013-07-20T00:39:24'),
                     milestones._table[0]['release_date'])
    self.assertEqual(62, milestones._table[1]['milestone'])
    self.assertEqual(3202, milestones._table[1]['branch'])
    self.assertEqual('62.0.3202.101', milestones._table[1]['version_number'])
    self.assertEqual(utils.ParseIsoFormatDate('2017-11-17T01:03:27'),
                     milestones._table[1]['release_date'])
    self.assertEqual(103, milestones._table[2]['milestone'])
    self.assertEqual(2304, milestones._table[2]['branch'])
    self.assertEqual('103.0.0.250', milestones._table[2]['version_number'])
    self.assertEqual(utils.ParseIsoFormatDate('2103-07-20T00:39:24'),
                     milestones._table[2]['release_date'],)

  def testLatest_milestone(self):
    latest_milestone = self.milestone_info.latest_milestone
    self.assertEqual(103, latest_milestone)

  def testGetLatestMilestoneBeforeDate(self):
    version = self.milestone_info.GetLatestMilestoneBeforeDate(
        utils.ParseDate('2017-10-01'))
    self.assertEqual(13, version)

  def testGetEarliestMilestoneAfterDate(self):
    version = self.milestone_info.GetEarliestMilestoneAfterDate(
        utils.ParseDate('2017-12-01'))
    self.assertEqual(103, version)

  def testGetVersionNumberFromMilestone(self):
    self.assertEqual(
        '103.0.0.250', self.milestone_info.GetVersionNumberFromMilestone(103))
