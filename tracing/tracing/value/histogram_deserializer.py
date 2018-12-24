# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from tracing.value import histogram
from tracing.value import histogram_serializer
from tracing.value.diagnostics import diagnostic


def Deserialize(dct):
  deserializer = HistogramDeserializer(dct)
  return {histogram.Histogram.FromDict(h, deserializer)
          for h in dct[histogram_serializer.HISTOGRAMS_TAG]}


class HistogramDeserializer(object):
  def __init__(self, dct):
    self._names = dct[histogram_serializer.NAMES_TAG]
    self._diagnostics_by_id = {}
    diagnostics_by_type = dct[histogram_serializer.DIAGNOSTICS_TAG]
    for type_name, diagnostics_by_name in diagnostics_by_type.items():
      for name, diagnostics_by_id in diagnostics_by_name.items():
        for i, diag_dict in diagnostics_by_id.items():
          diag = diagnostic.FromDict(type_name, diag_dict, self)
          self._diagnostics_by_id[str(i)] = {name: diag}

  def GetNameById(self, i):
    return self._names[i]

  def GetDiagnosticById(self, i):
    return self._diagnostics_by_id[str(i)]
