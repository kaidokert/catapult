# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections
import sys

from tracing.value import histogram
from tracing.value import histogram_set


def _GetOrCreateHistogram(histograms, name):
  hs = histograms.GetHistogramsNamed(name)
  if len(hs) > 1:
    raise Exception('Too many Histograms named %s' % name)

  if len(hs) == 1:
    return hs[0]

  hist = histogram.Histogram(name, 'sizeInBytes_smallerIsBetter')
  hist.CustomizeSummaryOptions(dict(std=False, min=False, max=False))
  histograms.AddHistogram(hist)
  return hist


def _Recurse(obj, seen_set, histograms):
  if id(obj) in seen_set:
    return 0
  seen_set.add(id(obj))

  size = sys.getsizeof(obj)

  if isinstance(obj, dict):
    for objkey, objvalue in obj.iteritems():
      size += _Recurse(objkey, seen_set, histograms)
      size += _Recurse(objvalue, seen_set, histograms)
  elif isinstance(obj, (tuple, list, set, frozenset, collections.deque)):
    # Can't use collections.Iterable because strings are iterable, but
    # sys.getsizeof() already handles strings, we don't need to iterate over
    # them.
    for elem in obj:
      size += _Recurse(elem, seen_set, histograms)
  elif hasattr(obj.__class__, '__slots__'):
    for slot in obj.__class__.__slots__:
      if not hasattr(obj, slot):
        continue
      size += _Recurse(getattr(obj, slot), seen_set, histograms)
  elif hasattr(obj, '__dict__'):
    size += _Recurse(obj.__dict__, seen_set, histograms)

  if not str(type(obj)).startswith('<class '):
    return size

  hist = _GetOrCreateHistogram(histograms, type(obj).__name__)
  hist.AddSample(size)
  return 0


def HeapMetric(root):
  histograms = histogram_set.HistogramSet()
  _Recurse(root, set(), histograms)
  return histograms
