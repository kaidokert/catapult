# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

from tracing.value import histogram
from tracing.value import histogram_set
from tracing.value.diagnostics import generic_set
from tracing.value.diagnostics import reserved_infos


def ConvertGtestJson(gtest_json):
  """Convert JSON from a gtest perf test to Histograms.

  Incoming data is in the following format:
  {
    'metric1': {
      'units': 'unit1',
      'traces': {
        'story1': ['mean', 'std_dev'],
        'story2': ['mean', 'std_dev'],
      },
      'important': ['testcase1', 'testcase2'],
    },
    'metric2': {
      'units': 'unit2',
      'traces': {
        'story1': ['mean', 'std_dev'],
        'story2': ['mean', 'std_dev'],
      },
      'important': ['testcase1', 'testcase2'],
    },
    ...
  }
  We ignore the 'important' fields and just assume everything should be
  considered important.

  We also don't bother adding any reserved diagnostics like mastername in this
  script since that should be handled by the upload script.

  Args:
    gtest_json: A JSON dict containing perf output from a gtest

  Returns:
    A HistogramSet containing equivalent histograms and diagnostics
  """

  hs = histogram_set.HistogramSet()

  for metric, metric_data in gtest_json.iteritems():
    # Maintain the same unit if we're able to find an exact match, otherwise
    # use 'unitless'.
    # TODO(https://crbug.com/843643): Add matching even if the strings aren't
    # identical and look into determining whether to add _biggerIsBetter or
    # _smallerIsBetter.
    unit = metric_data.get('units')
    unit = unit if unit in histogram.UNIT_NAMES else 'unitless'

    for story, story_data in metric_data['traces'].iteritems():
      # We should only ever have the mean and standard deviation here.
      assert len(story_data) == 2
      h = histogram.Histogram(metric, unit)
      h.diagnostics[reserved_infos.STORIES.name] = generic_set.GenericSet(
          [story])
      mean = float(story_data[0])
      h.AddSample(mean)

      # We're given the mean and standard deviation, but Histograms work by
      # taking in samples and calculating the standard deviation on the fly
      # (i.e. we can't just set the standard deviation). So, add two dummy
      # values that should leave the mean unchanged and give us the desired
      # standard deviation.
      std_dev = float(story_data[1])
      h.AddSample(mean + std_dev)
      h.AddSample(mean - std_dev)
      hs.AddHistogram(h)

  return hs

def ConvertGtestJsonFile(filepath):
  """Convert JSON in a file from a gtest perf test to Histograms.

  Contents of the given file will be overwritten with the new Histograms data.

  Args:
    filepath: The filepath to the JSON file to read/write from/to.
  """
  with open(filepath, 'r') as f:
    data = json.load(f)
  histograms = ConvertGtestJson(data)
  with open(filepath, 'w') as f:
    json.dump(histograms.AsDicts(), f)
