#!/usr/bin/env python
# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import os
import sys
import re

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from tracing.model import get_revision

def Main(argv):
  parser = argparse.ArgumentParser(description='Finds revision of trace files')
  parser.add_argument('trace_file_dir',
                      help='A directory containing trace files')
  parser.add_argument('--filename', default='revisionMap', type=str,
                      help='Output file name (no extension)')

  args = parser.parse_args(argv[1:])
  trace_file_dir = os.path.abspath(args.trace_file_dir)

  if os.path.isdir(trace_file_dir):
    traces = [os.path.join(trace_file_dir, trace)
              for trace in os.listdir(trace_file_dir)]
  else:
    print "Given path is not a directory"

  output_file = args.filename + '.csv'
  regex = re.compile(r'(?:{#(\d+)})')

  with open(output_file, 'wb') as csvfile:
    csvfile.write('FileName, Revision')
    for trace in traces:
      revision = regex.search(get_revision.GetRevision(trace))
      csvfile.write(os.path.basename(trace) + ", " + revision.group(1))

if __name__ == '__main__':
  sys.exit(Main(sys.argv))
