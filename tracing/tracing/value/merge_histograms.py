# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import time
import json
import os
import sys

import tracing_project
import vinn

_MERGE_HISTOGRAMS_CMD_LINE = os.path.join(
    os.path.dirname(__file__), 'merge_histograms_cmdline.html')


def MergeHistograms(json_path, groupby=()):
  """Merge Histograms.

  Args:
    json_path: Path to a HistogramSet JSON file.
    groupby: Array of grouping keys (name, benchmark, time, storyset_repeat,
             story_repeat, story, tir, label)
  Returns:
    HistogramSet dicts of the merged Histograms.
  """
  t0 = time.time()
  result = vinn.RunFile(
      _MERGE_HISTOGRAMS_CMD_LINE,
      source_paths=list(tracing_project.TracingProject().source_paths),
      js_args=[os.path.abspath(json_path)] + list(groupby))
  t1 = time.time()
  print 'MERGING IN JS %s' % (t1 - t0)
  if result.returncode != 0:
    sys.stderr.write(result.stdout)
    raise Exception('vinn merge_histograms_cmdline.html returned ' +
                    str(result.returncode))
  t0 = time.time()
  dicts = json.loads(result.stdout)
  t1 = time.time()
  print 'DESERIALIZING MERGED %s' % (t1 - t0)
  return dicts
