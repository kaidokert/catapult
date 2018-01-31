# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import logging

from telemetry.internal.results import output_formatter
from tracing.value.diagnostics import reserved_infos


class DummyValue(object):
  def __init__(self, name):
    self.name = name


class HistogramSetJsonOutputFormatter(output_formatter.OutputFormatter):
  def __init__(self, output_stream, metadata, reset_results):
    super(HistogramSetJsonOutputFormatter, self).__init__(output_stream)
    self._metadata = metadata
    self._reset_results = reset_results

  def Format(self, page_test_results):
    histograms = page_test_results.AsHistogramDicts()
    for histogram in histograms:
      is_first_result = histogram.diagnostics[
          reserved_infos.STORYSET_REPEATS.name][0] == 0
      if not page_test_results._value_can_be_added_predicate(
          DummyValue(histogram.name), is_first_result):
        del histogram

    self._output_stream.seek(0)
    if not self._reset_results:
      existing = self._output_stream.read()
      self._output_stream.seek(0)
      if existing:
        try:
          histograms += json.loads(existing)
        except ValueError:
          logging.warn('Found existing histograms json but failed to parse it.')
    json.dump(histograms, self._output_stream)
