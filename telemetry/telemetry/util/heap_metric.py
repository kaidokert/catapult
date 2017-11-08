# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import codecs
import collections
import sys
import time

from tracing.value import histogram
from tracing.value import histogram_set
from tracing.value.diagnostics import reserved_infos
from tracing_build import vulcanize_histograms_viewer


def _IsUserDefinedInstance(obj):
  return str(type(obj)).startswith('<class ')


class _HeapMetric(object):
  __slots__ = '_seen', '_histograms'

  def __init__(self):
    self._seen = set()
    self._histograms = None

  def Run(self, root):
    self._histograms = histogram_set.HistogramSet()
    total_hist = self._GetOrCreateHistogram('heap')
    total_hist.diagnostics['breakdown'] = histogram.RelatedNameMap()
    total_breakdown = histogram.Breakdown()
    total_size = self._Recurse(
        root, total_hist.diagnostics['breakdown'], total_breakdown)

    total_breakdown.Set('other', total_size)
    total_size += sum(
        hist.sum for hist in self._histograms if hist is not total_hist)
    total_hist.AddSample(total_size, dict(breakdown=total_breakdown))

    self._histograms.AddSharedDiagnostic(
        reserved_infos.TRACE_START.name,
        histogram.DateRange(time.time() * 1000))
    return self._histograms

  def _GetOrCreateHistogram(self, name):
    hs = self._histograms.GetHistogramsNamed(name)
    if len(hs) > 1:
      raise Exception('Too many Histograms named %s' % name)

    if len(hs) == 1:
      return hs[0]

    hist = histogram.Histogram(name, 'sizeInBytes_smallerIsBetter')
    hist.CustomizeSummaryOptions(dict(std=False, min=False, max=False))
    self._histograms.AddHistogram(hist)
    return hist

  def _Recurse(self, obj, parent_related_names, parent_breakdown):
    if id(obj) in self._seen:
      return 0
    self._seen.add(id(obj))

    size = sys.getsizeof(obj)

    related_names = parent_related_names
    breakdown = parent_breakdown
    hist = None
    if _IsUserDefinedInstance(obj):
      type_name = type(obj).__name__
      hist = self._GetOrCreateHistogram('heap:' + type_name)
      related_names = histogram.RelatedNameMap()
      hist.diagnostics['breakdown'] = related_names
      breakdown = histogram.Breakdown()

    if isinstance(obj, dict):
      for objkey, objvalue in obj.iteritems():
        size += self._Recurse(objkey, related_names, breakdown)
        size += self._Recurse(objvalue, related_names, breakdown)
    elif isinstance(obj, (tuple, list, set, frozenset, collections.deque)):
      # Can't use collections.Iterable because strings are iterable, but
      # sys.getsizeof() already handles strings, we don't need to iterate over
      # them.
      for elem in obj:
        size += self._Recurse(elem, related_names, breakdown)
    elif hasattr(obj.__class__, '__slots__'):
      for slot in obj.__class__.__slots__:
        if hasattr(obj, slot):
          size += self._Recurse(getattr(obj, slot), related_names, breakdown)
    elif hasattr(obj, '__dict__'):
      size += self._Recurse(obj.__dict__, related_names, breakdown)

    if hist is None:
      return size

    parent_related_names.Set(type_name, hist.name)
    parent_breakdown.Set(type_name, parent_breakdown.Get(type_name) + size)
    breakdown.Set('other', size - sum(subsize for _, subsize in breakdown))
    hist.AddSample(size, dict(breakdown=breakdown))
    return size


def HeapMetric(root, label=None, html_filename=None):
  histograms = _HeapMetric().Run(root)

  if label:
    histograms.AddSharedDiagnostic(
        reserved_infos.LABELS.name, histogram.GenericSet([label]))

  if html_filename:
    output_stream = codecs.open(html_filename, mode='ar+', encoding='utf-8')
    vulcanize_histograms_viewer.VulcanizeAndRenderHistogramsViewer(
        histograms.AsDicts(), output_stream)

  return histograms
