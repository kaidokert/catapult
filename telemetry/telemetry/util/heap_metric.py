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
  __slots__ = '_diagnostics_callback', '_histograms', '_seen'

  def __init__(self, diagnostics_callback):
    self._diagnostics_callback = diagnostics_callback
    self._histograms = None
    self._seen = set()

  def Run(self, root):
    self._histograms = histogram_set.HistogramSet()
    total_hist = self._GetOrCreateHistogram('heap')
    total_hist.diagnostics['breakdown'] = histogram.RelatedNameMap()
    total_breakdown = histogram.Breakdown()
    total_size = self._Recurse(
        root, total_hist.diagnostics['breakdown'], total_breakdown)
    other_size = total_size - sum(subsize for _, subsize in total_breakdown)

    if other_size:
      total_breakdown.Set('other', other_size)
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

      related_names = hist.diagnostics.get('breakdown')
      if related_names is None:
        related_names = histogram.RelatedNameMap()
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

    # It is possible to subclass builtin types like dict and add properties to
    # them, so handle __dict__ and __slots__ even if obj is a dict/list/etc.

    dict_breakdown = None
    if hasattr(obj, '__dict__'):
      dict_breakdown = histogram.Breakdown()
      size += sys.getsizeof(obj.__dict__)
      for dkey, dvalue in obj.__dict__.iteritems():
        size += self._Recurse(dkey, related_names, breakdown)
        dsize = self._Recurse(dvalue, related_names, breakdown)
        dict_breakdown.Set(dkey, dsize)
        size += dsize
      size += self._Recurse(obj.__dict__, related_names, breakdown)

    # It is possible for a class to use both __slots__ and __dict__ by listing
    # __dict__ as a slot.

    slots_breakdown = None
    if hasattr(obj.__class__, '__slots__'):
      slots_breakdown = histogram.Breakdown()
      for slot in obj.__class__.__slots__:
        if slot == '__dict__':
          # obj.__dict__ was already handled
          continue
        if not hasattr(obj, slot):
          continue
        slot_size = self._Recurse(getattr(obj, slot), related_names, breakdown)
        slots_breakdown.Set(slot, slot_size)
        size += slot_size

    if hist:
      if len(related_names):
        hist.diagnostics['breakdown'] = related_names

      parent_related_names.Set(type_name, hist.name)
      parent_breakdown.Set(type_name, parent_breakdown.Get(type_name) + size)

      breakdown.Set('other', size - sum(subsize for _, subsize in breakdown))

      sample_diagnostics = {'breakdown': breakdown}
      if dict_breakdown:
        sample_diagnostics['__dict__'] = dict_breakdown
      if slots_breakdown:
        sample_diagnostics['__slots__'] = slots_breakdown
      if self._diagnostics_callback:
        sample_diagnostics.update(self._diagnostics_callback(obj))

      hist.AddSample(size, sample_diagnostics)

    return size


def HeapMetric(root, label=None, html_filename=None, diagnostics_callback=None):
  histograms = _HeapMetric(diagnostics_callback).Run(root)

  if label:
    histograms.AddSharedDiagnostic(
        reserved_infos.LABELS.name, histogram.GenericSet([label]))

  if html_filename:
    output_stream = codecs.open(html_filename, mode='ar+', encoding='utf-8')
    vulcanize_histograms_viewer.VulcanizeAndRenderHistogramsViewer(
        histograms.AsDicts(), output_stream)

  return histograms
