#!/usr/bin/python2


import argparse
import re
import sys
import subprocess


def main(args):
  fetch_tool = FetchTool()
  return fetch_tool.Main(args)


class FetchTool(object):
  def __init__(self):
    self.processor_architecture = 'arm'
    self.chrome_type = 'Stable'  # ensure that the first character is capitalized
    self.args = argparse.Namespace()
    self.uris = []

  def Main(self, args):
    if not self.IsGsutilInstalled():
      print 'gsutil is not installed, please install it and try again'
      exit(1)

    self.ParseArgs(args)
    try:
      self.GetCloudStorageURIs()
      self.DownloadAPKsFromURIs()
      return 0
    except KeyboardInterrupt:
      print 'interrupted, exiting...'
      return 130
    # TODO(wangge): do we need to catch other type of exception

  def IsGsutilInstalled(self):
    return subprocess.call(['which', 'gsutil']) == 0

  def ParseArgs(self, argv):
    parser = argparse.ArgumentParser(description='tool to donwload different versions of chrome')
    parser.add_argument('from_milestone', type=int, help="starting milestones")
    parser.add_argument('to_milestone', type=int, help='ending milestone')
    self.args = parser.parse_args(argv)

  def DownloadAPKsFromURIs(self):
    def GetAPKName(gs_uri):
      return '_'.join(gs_uri.split('/')[-3:])

    for uri in self.uris:
      # TODO(wangge): How to fail back if the download is not successful?
      try:
        subprocess.call(['gsutil', 'cp', uri, 'out/' + GetAPKName(uri)])
      except subprocess.CalledProcessError:
        print 'download not successful, exiting'
        exit(1)
      print GetAPKName(uri) + ' has been downloaded'

    self.uris = []  # reset the uris when the download is completed

  def GetLatestVersionURI(self, milestone_num):
    subdirectory_name = 'B0urB0N' if milestone_num > 44 else 'C4MPAR1'
    # 'C4MPAR1' is used to store milestone 27 to milestone 44, B0urB0N is used to store versions
    # from milestone 45 onwards
    try:
      all_uris = subprocess.check_output(['gsutil', 'ls',
                                          'gs://chrome-signed/android-%s/%s*/%s/Chrome%s.apk' %
                                          (subdirectory_name, milestone_num,
                                           self.processor_architecture, self.chrome_type)])
    except subprocess.CalledProcessError:
      print 'Failed getting the latest version of uri for the milestone number: ' + milestone_num
      exit(1)

    # remove empty strings
    all_uris = [uri for uri in all_uris.split('\n') if not re.match(r'^\s*$', uri)]
    # assuming that the last uri is the latest one
    return all_uris[-1]

  def GetCloudStorageURIs(self):
    """
    set the `uris` variable for FetchTool instance
    """
    print "Getting the storage URI, this process might take some time, please wait patiently"
    for milestone in range(self.args.from_milestone, self.args.to_milestone):
      self.uris.append(self.GetLatestVersionURI(milestone))


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
