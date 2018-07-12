#!/usr/bin/env python
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Tool for downloading different versions of Chrome.

"""

import argparse
import re
import subprocess
import sys


PROCESSOR_ARCHITECTURE = 'arm'
CHROME_TYPE = 'Stable'


def DownloadAPKsFromURIs(uris):
  """Used to download the APKs from google cloud into the out folder.

  Args:
    uris: List of google cloud URIs
  """
  def GetAPKName(gs_uri):
    return '_'.join(gs_uri.split('/')[-3:])

  for uri in uris:
    # TODO(wangge): How to fail back if the download is not successful?
    try:
      subprocess.call(['gsutil', 'cp', uri, 'out/' + GetAPKName(uri)])
    except subprocess.CalledProcessError:
      print 'download is not successful, exiting'
      exit(1)
    print GetAPKName(uri) + ' has been downloaded'


def GetLatestVersionURI(milestone_num):
  """Helper function for `GetCloudStorageURIs`.

  Args:
    milestone_num: Number representing the milestone.

  Returns:
    The URI for the latest version of Chrome for a given milestone.
  """
  subdirectory_name = 'B0urB0N' if milestone_num > 44 else 'C4MPAR1'
  # 'C4MPAR1' is used to store milestone 27 to milestone 44,
  # B0urB0N is used to store versions from milestone 45 onwards
  try:
    all_uris = subprocess.check_output(
        ['gsutil', 'ls', 'gs://chrome-signed/android-%s/%s*/%s/Chrome%s.apk' %
         (subdirectory_name, milestone_num, PROCESSOR_ARCHITECTURE, CHROME_TYPE)
        ])
  except subprocess.CalledProcessError:
    print ('Failed getting the latest version of uri for the milestone number: '
           + milestone_num)
    exit(1)

  # remove empty strings
  all_uris \
    = [uri for uri in all_uris.split('\n') if not re.match(r'^\s*$', uri)]
  # assuming that the last uri is the latest one
  return all_uris[-1]


def GetCloudStorageURIs(from_milestone, to_milestone):
  print ('Getting the storage URI, this process might '
         'take some time, please wait patiently')
  uris = []
  for milestone in range(from_milestone, to_milestone):
    uris.append(GetLatestVersionURI(milestone))

  return uris


def IsGsutilInstalled():
  return subprocess.call(['which', 'gsutil']) == 0


def main(args):
  if not IsGsutilInstalled():
    return 'gsutil is not installed, please install it and try again'

  parser = argparse.ArgumentParser(
      description='tool to download different versions of chrome')
  parser.add_argument('from_milestone', type=int, help='starting milestones')
  parser.add_argument('to_milestone', type=int, help='ending milestone')
  args = parser.parse_args(args)

  try:
    all_uris = GetCloudStorageURIs(args.from_milestone, args.to_milestone)
    DownloadAPKsFromURIs(all_uris)
    return 0
  except KeyboardInterrupt:
    print 'interrupted, exiting...'
    return 130
  # TODO(wangge): do we need to catch other type of exception


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
