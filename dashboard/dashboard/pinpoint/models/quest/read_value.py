# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

from dashboard.common import histogram_helpers
from dashboard.pinpoint.models.quest import execution
from dashboard.pinpoint.models.quest import quest
from dashboard.services import isolate
from tracing.value import histogram_set
from tracing.value.diagnostics import diagnostic_ref
from tracing.value.diagnostics import reserved_infos


class ReadValueError(Exception):

  pass


class ReadHistogramsJsonValue(quest.Quest):

  def __init__(self, hist_name=None, tir_label=None,
               story=None, statistic=None):
    self._hist_name = hist_name
    self._tir_label = tir_label
    self._story = story
    self._statistic = statistic

  def __eq__(self, other):
    return (isinstance(other, type(self)) and
            self._hist_name == other._hist_name and
            self._tir_label == other._tir_label and
            self._story == other._story and
            self._statistic == other._statistic)

  def __str__(self):
    return 'Values'

  def Start(self, change, isolate_server=None, isolate_hash=None):
    del change

    # TODO(dtu): Remove after data migration.
    # isolate_server and isolate_hash are required arguments.
    assert isolate_hash
    if not isolate_server:
      isolate_server = 'https://isolateserver.appspot.com'

    return _ReadHistogramsJsonValueExecution(
        self._hist_name, self._tir_label, self._story,
        self._statistic, isolate_server, isolate_hash)

  @classmethod
  def FromDict(cls, arguments):
    chart = arguments.get('chart')
    tir_label = arguments.get('tir_label')
    trace = arguments.get('trace')
    statistic = arguments.get('statistic')
    return cls(chart, tir_label, trace, statistic)


class _ReadHistogramsJsonValueExecution(execution.Execution):

  def __init__(self, hist_name, tir_label, story,
               statistic, isolate_server, isolate_hash):
    super(_ReadHistogramsJsonValueExecution, self).__init__()
    self._hist_name = hist_name
    self._tir_label = tir_label
    self._story = story
    self._statistic = statistic
    self._isolate_server = isolate_server
    self._isolate_hash = isolate_hash

    self._trace_urls = []

  def _AsDict(self):
    if not self._trace_urls:
      return {}
    # TODO(dtu): Remove after data migration.
    if not hasattr(self, '_isolate_server'):
      self._isolate_server = 'https://isolateserver.appspot.com'
    return {
        'isolate_server': self._isolate_server,
        'traces': self._trace_urls,
    }

  def _Poll(self):
    # TODO(dtu): Remove after data migration.
    if not hasattr(self, '_isolate_server'):
      self._isolate_server = 'https://isolateserver.appspot.com'
    # TODO(simonhatch): Switch this to use the new perf-output flag instead
    # of the chartjson one. They're functionally equivalent, just new name.
    histogram_dicts = _RetrieveOutputJson(
        self._isolate_server, self._isolate_hash, 'chartjson-output.json')
    histograms = histogram_set.HistogramSet()
    histograms.ImportDicts(histogram_dicts)
    histograms.ResolveRelatedHistograms()

    matching_histograms = histograms.GetHistogramsNamed(self._hist_name)

    # Get and cache any trace URLs.
    unique_trace_urls = set()
    for hist in histograms:
      trace_urls = hist.diagnostics.get(reserved_infos.TRACE_URLS.name)
      # TODO(simonhatch): Remove this sometime after May 2018. We had a
      # brief period where the histograms generated by tests had invalid
      # trace_urls diagnostics. If the diagnostic we get back is just a ref,
      # then skip.
      # https://github.com/catapult-project/catapult/issues/4243
      if trace_urls and not isinstance(
          trace_urls, diagnostic_ref.DiagnosticRef):
        unique_trace_urls.update(trace_urls)

    sorted_urls = sorted(unique_trace_urls)
    self._trace_urls = [
        {'name': t.split('/')[-1], 'url': t} for t in sorted_urls]

    # Filter the histograms by tir_label and story. Getting either the
    # tir_label or the story from a histogram involves pulling out and
    # examining various diagnostics associated with the histogram.
    tir_label = self._tir_label or ''

    matching_histograms = [
        h for h in matching_histograms
        if tir_label == histogram_helpers.GetTIRLabelFromHistogram(h)]


    # If no story is supplied, we're looking for a summary metric so just match
    # on name and tir_label. This is equivalent to the chartjson condition that
    # if no story is specified, look for "summary".
    if self._story:
      matching_histograms = [
          h for h in matching_histograms
          if self._story == _GetStoryFromHistogram(h)]

    # Have to pull out either the raw sample values, or the statistic
    result_values = []
    for h in matching_histograms:
      result_values.extend(self._GetValuesOrStatistic(h))

    if not result_values and self._hist_name:
      name = 'histogram: %s' % self._hist_name
      if tir_label:
        name += ' tir_label: %s' % tir_label
      if self._story:
        name += ' story: %s' % self._story
      raise ReadValueError('Could not find values matching: %s' % name)

    self._Complete(result_values=tuple(result_values))

  def _GetValuesOrStatistic(self, hist):
    if not self._statistic:
      return hist.sample_values

    if not hist.sample_values:
      return []

    # TODO(simonhatch): Use Histogram.getStatisticScalar when it's ported from
    # js.
    if self._statistic == 'avg':
      return [hist.running.mean]
    elif self._statistic == 'min':
      return [hist.running.min]
    elif self._statistic == 'max':
      return [hist.running.max]
    elif self._statistic == 'sum':
      return [hist.running.sum]
    elif self._statistic == 'std':
      return [hist.running.stddev]
    elif self._statistic == 'count':
      return [hist.running.count]
    raise ReadValueError('Unknown statistic type: %s' % self._statistic)


class ReadGraphJsonValue(quest.Quest):

  def __init__(self, chart, trace):
    self._chart = chart
    self._trace = trace

  def __eq__(self, other):
    return (isinstance(other, type(self)) and
            self._chart == other._chart and
            self._trace == other._trace)

  def __str__(self):
    return 'Values'

  def Start(self, change, isolate_server=None, isolate_hash=None):
    del change

    # TODO(dtu): Remove after data migration.
    # isolate_server and isolate_hash are required arguments.
    assert isolate_hash
    if not isolate_server:
      isolate_server = 'https://isolateserver.appspot.com'

    return _ReadGraphJsonValueExecution(
        self._chart, self._trace, isolate_server, isolate_hash)

  @classmethod
  def FromDict(cls, arguments):
    chart = arguments.get('chart')
    trace = arguments.get('trace')
    if not (chart or trace):
      return None
    if chart and not trace:
      raise TypeError('"chart" specified but no "trace" given.')
    if trace and not chart:
      raise TypeError('"trace" specified but no "chart" given.')
    return cls(chart, trace)


class _ReadGraphJsonValueExecution(execution.Execution):

  def __init__(self, chart, trace, isolate_server, isolate_hash):
    super(_ReadGraphJsonValueExecution, self).__init__()
    self._chart = chart
    self._trace = trace
    self._isolate_server = isolate_server
    self._isolate_hash = isolate_hash

  def _AsDict(self):
    # TODO(dtu): Remove after data migration.
    if not hasattr(self, '_isolate_server'):
      self._isolate_server = 'https://isolateserver.appspot.com'
    return {'isolate_server': self._isolate_server}

  def _Poll(self):
    # TODO(dtu): Remove after data migration.
    if not hasattr(self, '_isolate_server'):
      self._isolate_server = 'https://isolateserver.appspot.com'
    graphjson = _RetrieveOutputJson(
        self._isolate_server, self._isolate_hash, 'chartjson-output.json')

    if self._chart not in graphjson:
      raise ReadValueError('The chart "%s" is not in the results.' %
                           self._chart)
    if self._trace not in graphjson[self._chart]['traces']:
      raise ReadValueError('The trace "%s" is not in the results.' %
                           self._trace)
    result_value = float(graphjson[self._chart]['traces'][self._trace][0])

    self._Complete(result_values=(result_value,))


def _RetrieveOutputJson(isolate_server, isolate_hash, filename):
  output_files = json.loads(isolate.Retrieve(
      isolate_server, isolate_hash))['files']

  if filename not in output_files:
    raise ReadValueError("The test didn't produce %s." % filename)
  output_json_isolate_hash = output_files[filename]['h']
  return json.loads(isolate.Retrieve(isolate_server, output_json_isolate_hash))


def _GetStoryFromHistogram(hist):
  stories = hist.diagnostics.get(reserved_infos.STORIES.name)
  if stories and len(stories) == 1:
    return list(stories)[0]
  return None
