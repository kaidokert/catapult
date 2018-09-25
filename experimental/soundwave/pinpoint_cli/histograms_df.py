# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import pandas

from tracing.value import histogram_set
from tracing.value.diagnostics import generic_set


_PROPERTIES = (
    ('name', 'name'),
    ('unit', 'unit'),
    ('mean', 'average'),
    ('stdev', 'standard_deviation'),
    ('count', 'num_values')
)
_DIAGNOSTICS = (
    ('run_label', 'labels'),
    ('story', 'stories'),
    ('benchmark_start', 'benchmarkStart'),
    ('device_id', 'deviceIds'),
    ('trace_url', 'traceUrls')
)
COLUMNS = tuple(key for key, _ in _PROPERTIES) + tuple(
    key for key, _ in _DIAGNOSTICS)


def _DiagnosticValue(value):
  if isinstance(value, generic_set.GenericSet):
    return ','.join(str(v) for v in value)
  else:
    return str(value)


def IterRows(histogram_dicts):
  histograms = histogram_set.HistogramSet()
  histograms.ImportDicts(histogram_dicts)
  histograms.ResolveRelatedHistograms()
  for hist in histograms:
    row = [getattr(hist, name) for _, name in _PROPERTIES]
    row.extend(
        _DiagnosticValue(hist.diagnostics.get(name))
        for _, name in _DIAGNOSTICS)
    yield tuple(row)


def DataFrame(histogram_dicts):
  df = pandas.DataFrame.from_records(
      IterRows(histogram_dicts),
      columns=COLUMNS)
  df['benchmark_start'] = pandas.to_datetime(df['benchmark_start'])
  return df

