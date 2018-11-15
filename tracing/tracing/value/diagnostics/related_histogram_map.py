# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from tracing.value.diagnostics import diagnostic


class RelatedHistogramMap(diagnostic.Diagnostic):
  __slots__ = '_histograms_by_name',

  def __init__(self):
    super(RelatedHistogramMap, self).__init__()
    self._histograms_by_name = {}

  def Get(self, name):
    return self._histograms_by_name.get(name)

  def Set(self, name, hist):
    from tracing.value import histogram
    assert isinstance(hist, (histogram.Histogram, histogram.HistogramRef)), (
        'Expected Histogram or HistogramRef, found %s: "%r"',
        (type(hist).__name__, hist))
    self._histograms_by_name[name] = hist

  def Add(self, hist):
    self.Set(hist.name, hist)

  def __len__(self):
    return len(self._histograms_by_name)

  def __iter__(self):
    for name, hist in self._histograms_by_name.items():
      yield name, hist

  def Resolve(self, histograms, required=False):
    from tracing.value import histogram
    for name, hist in self:
      if not isinstance(hist, histogram.HistogramRef):
        continue

      guid = hist.guid
      hist = histograms.LookupHistogram(guid)
      if isinstance(hist, histogram.Histogram):
        self._histograms_by_name[name] = hist
      else:
        assert not required, ('Missing required Histogram %s' % guid)

  def _AsDictInto(self, d):
    d['values'] = {}
    for name, hist in self:
      d['values'][name] = hist.guid

  @staticmethod
  def FromDict(d):
    from tracing.value import histogram
    result = RelatedHistogramMap()
    for name, guid in d['values'].items():
      result.Set(name, histogram.HistogramRef(guid))
    return result
