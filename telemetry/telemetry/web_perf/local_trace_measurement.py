# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


import logging
import os
import time

from telemetry.value import common_value_helpers
from telemetry.web_perf import story_test
from telemetry.web_perf import timeline_based_measurement
from tracing.metrics import metric_runner


# class LocalTraceMeasurement(story_test.StoryTest):
class LocalTraceMeasurement(
    timeline_based_measurement.TimelineBasedMeasurement):
  """TODO(rmistry): Fix PyDoc.

  A class for creating story tests.

  The overall test run control flow follows this order:
    test.WillRunStory
    state.WillRunStory
    state.RunStory
    test.Measure
    state.DidRunStory
    test.DidRunStory
  """

  def __init__(self, options, results_wrapper=None):
    self._tbm_options = options

  def WillRunStory(self, platform):
    """Executes any necessary actions before running the story."""
    pass

  def Measure(self, platform, results):
    """Collect all possible metrics and added them to results."""
    filename = "/repos/chromium/src/tools/perf/https___www_google_com_2018-04-17_10-46-41_2992.html"

    metrics = self._tbm_options.GetTimelineBasedMetrics()
    extra_import_options = {
        'trackDetailedModelStats': True
    }
    trace_size_in_mib = os.path.getsize(filename) / (2 ** 20)
    # Bails out on trace that are too big. See crbug.com/812631 for more
    # details.
    if trace_size_in_mib > 400:
      results.Fail('Trace size is too big: %s MiB' % trace_size_in_mib)
      return

    logging.warning('Starting to compute metrics on trace')
    start = time.time()
    mre_result = metric_runner.RunMetric(
        filename, metrics, extra_import_options,
        report_progress=False)
    logging.warning('Processing resulting traces took %.3f seconds' % (
        time.time() - start))
    page = results.current_page

    for f in mre_result.failures:
      results.Fail(f.stack)

    histogram_dicts = mre_result.pairs.get('histograms', [])
    results.ImportHistogramDicts(histogram_dicts)

    for d in mre_result.pairs.get('scalars', []):
      results.AddValue(common_value_helpers.TranslateScalarValue(d, page))

  def DidRunStory(self, platform, results):
    """Override to do any action after running the story, e.g., clean up.

    This is run after state.DidRunStory. And this is always called even if the
    test run failed. The |results| object can be used to stored debugging info
    related to run.
    Args:
      platform: The platform that the story will run on.
      results: The results of running the story.
    """
    pass
