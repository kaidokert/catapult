# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


HISTOGRAMS_TAG = 'h'
NAMES_TAG = 'n'
DIAGNOSTICS_TAG = 'd'


def Serialize(histograms):
  serializer = HistogramSerializer()
  dct = {
      NAMES_TAG: serializer._names,
      DIAGNOSTICS_TAG: serializer._diagnostics_by_type,
      HISTOGRAMS_TAG: [h.AsDict(serializer) for h in histograms],
  }
  for diagnostics_by_name in dct[DIAGNOSTICS_TAG].values():
    for diagnostics_by_id in diagnostics_by_name.values():
      for did, diag in diagnostics_by_id.items():
        diagnostics_by_id[did] = diag.AsDict(serializer)
  return dct


class HistogramSerializer(object):
  __slots__ = '_names', '_diagnostics_by_type', '_diagnostic_id'

  def __init__(self):
    self._names = []
    self._diagnostics_by_type = {}
    self._diagnostic_id = -1

  def GetNameId(self, name):
    if name in self._names:
      return self._names.index(name)
    self._names.append(name)
    return len(self._names) - 1

  def GetDiagnosticId(self, name, diag):
    type_name = diag.__class__.__name__
    diagnostics_by_name = self._diagnostics_by_type.setdefault(type_name, {})
    diagnostics_by_id = diagnostics_by_name.setdefault(name, {})
    for i, other in diagnostics_by_id.items():
      if other is diag or other == diag:
        return i

    self._diagnostic_id += 1
    diagnostics_by_id[self._diagnostic_id] = diag
    return self._diagnostic_id
