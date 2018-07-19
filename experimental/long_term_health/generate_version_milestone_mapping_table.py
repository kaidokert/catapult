#!/usr/bin/env python
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Tool for generating the full_milestone_info.csv.

"""

import csv
import datetime
import httplib
import json
import os
import re

LOG_COUNT = 10  # assuming that version is incremented within the first 10 logs
USELESS_CHAR_COUNT = 5
APP_DIR = os.path.normpath(os.path.dirname(__file__))


class MappingGenerationFailed(Exception):
  pass


def GetChromiumLog(revision, count=LOG_COUNT):
  """Used to get the git commit log for the given revision.

  Args:
    revision: the revision that you want the git log for
    count: the number of the git log that you want to get back
  Returns:
    list: a list of git logs
  """
  conn = httplib.HTTPSConnection('chromium.googlesource.com')
  conn.request('GET', '/chromium/src.git/+log'
                      '/%s?format=JSON&n=%s' % (revision, count))
  response = conn.getresponse()
  # we skip the rubbish character in the json that is sent back to us
  log_list = json.loads(response.read()[USELESS_CHAR_COUNT:])['log']
  return log_list


def GetBranchInfo(milestone, branch):
  """Used to get the latest version number and release date for a given branch.

  Args:
    milestone: the major version number
    branch: the latest branch corresponding with the milestone
  Returns:
    dict: version incrementing log info
  Raises:
    MappingGenerationFailed: this would be raised if
      no log is incrementing the version
  """
  # loop through the logs to get the first log
  # that increments the version number
  for log in GetChromiumLog('refs/branch-heads/%s' % branch):
    version_number = re.search(
        r'(?<=Incrementing VERSION to )[\d.]+', log['message'])
    if version_number:
      release_date = datetime.datetime.strptime(
          log['committer']['time'], '%a %b %d %X %Y').strftime('%d %b %Y')
      return (milestone, branch, version_number.group(0), release_date)
  #  raise exception if non of the log is relevant
  raise MappingGenerationFailed


def main():
  with open(os.path.join(APP_DIR, 'full_milestone_info.csv'), 'w') as new_table:
    writer = csv.writer(new_table)
    writer.writerow(['milestone', 'branch', 'version_number', 'release_date'])
    with open(os.path.join(
        APP_DIR, 'milestone_build_mapping_table.csv')) as milestone_build_table:
      reader = csv.reader(milestone_build_table)
      next(reader, None)  # skip the header line
      for milestone, branch in reader:
        writer.writerow(GetBranchInfo(milestone, branch))


if __name__ == '__main__':
  main()
