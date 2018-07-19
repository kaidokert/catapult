#!/usr/bin/env python
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Tool for generating the milestone, version number and release date table.

"""

import csv
import datetime
import httplib
import json
import re

LOG_COUNT = 10  # assuming that version is incremented within the first 10 logs
USELESS_CHAR_COUNT = 5


class MappingGenerationFailed(Exception):
  pass


def GetLog(build_number):
  """Used to get a dictionary with log info that increment the version.

  Args:
    build_number: the build number that we want to fetch log for
  Returns:
    dict: version incrementing log info
  Raises:
    MappingGenerationFailed: this would be raised if
      no log is incrementing the version
  """
  conn = httplib.HTTPSConnection('chromium.googlesource.com')
  conn.request('GET', '/chromium/src.git/+log/refs/branch-heads'
                      '/%s?format=JSON&n=%s' % (build_number, LOG_COUNT))
  response = conn.getresponse()
  # we skip the rubbish character in the json that is sent back to us
  log_list = json.loads(response.read()[USELESS_CHAR_COUNT:])['log']
  # loop through the logs to get the first log
  # that increments the version number
  for log in log_list:
    if re.search(r'(?<=Incrementing VERSION to )[\d.]+', log['message']):
      return log
  #  raise exception if non of the log is relevant
  raise MappingGenerationFailed


def GetReleaseDate(log):
  release_time = datetime.datetime.strptime(
      log['committer']['time'], '%a %b %d %X %Y')
  return release_time.strftime('%d %b %Y')


def GetVersionNumber(log):
  message = log['message']
  return re.search(
      r'(?<=Incrementing VERSION to )[\d.]+', message).group(0)


def main():
  with open('milestone_version_release_date_table.csv', 'w') as new_table:
    writer = csv.writer(new_table, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['milestone', 'build', 'version number', 'release date'])
    with open('milestone_build_mapping_table.csv') as milestone_build_table:
      reader = csv.reader(milestone_build_table)
      next(reader, None)  # skip the header line
      for row in reader:
        log = GetLog(row[1])
        writer.writerow(
            [row[0], row[1], GetReleaseDate(log), GetVersionNumber(log)])


if __name__ == '__main__':
  main()
