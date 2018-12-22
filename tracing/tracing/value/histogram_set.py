# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from tracing.value import histogram as histogram_module
from tracing.value import histogram_deserializer
from tracing.value import histogram_serializer
from tracing.value.diagnostics import all_diagnostics
from tracing.value.diagnostics import diagnostic
from tracing.value.diagnostics import diagnostic_ref
from tracing.value.diagnostics import generic_set

class HistogramSet(object):
  def __init__(self, histograms=()):
    self._histograms_by_guid = {}
    self._shared_diagnostics_by_guid = {}
    for hist in histograms:
      self.AddHistogram(hist)

  def CreateHistogram(self, name, unit, samples, **kw):
    hist = histogram_module.Histogram.Create(name, unit, samples, **kw)
    self.AddHistogram(hist)
    return hist

  @property
  def shared_diagnostics(self):
    return self._shared_diagnostics_by_guid.values()

  def RemoveOrphanedDiagnostics(self):
    orphans = set(self._shared_diagnostics_by_guid.keys())
    for h in self._histograms_by_guid.values():
      for d in h.diagnostics.values():
        if d.guid in orphans:
          orphans.remove(d.guid)
    for guid in orphans:
      del self._shared_diagnostics_by_guid[guid]

  def FilterHistograms(self, discard):
    self._histograms_by_guid = dict(
        (guid, hist)
        for guid, hist in self._histograms_by_guid.items()
        if not discard(hist))

  def AddHistogram(self, hist, diagnostics=None):
    if hist.guid in self._histograms_by_guid:
      raise ValueError('Cannot add same Histogram twice')

    if diagnostics:
      for name, diag in diagnostics.items():
        hist.diagnostics[name] = diag

    self._histograms_by_guid[hist.guid] = hist

  def AddSharedDiagnosticToAllHistograms(self, name, diag):
    for hist in self:
      hist.diagnostics[name] = diag

  def GetFirstHistogram(self):
    for histogram in self._histograms_by_guid.values():
      return histogram

  def GetHistogramsNamed(self, name):
    return [h for h in self if h.name == name]

  def GetHistogramNamed(self, name):
    hists = self.GetHistogramsNamed(name)
    if len(hists) == 0:
      return None
    if len(hists) > 1:
      raise ValueError(
          'Unexpectedly found multiple histograms named "' + name + '"')
    return hists[0]

  def GetSharedDiagnosticsOfType(self, typ):
    return [d for d in self.shared_diagnostics if isinstance(d, typ)]

  def LookupHistogram(self, guid):
    return self._histograms_by_guid.get(guid)

  def LookupDiagnostic(self, guid):
    return self._shared_diagnostics_by_guid.get(guid)

  def ResolveRelatedHistograms(self):
    histograms = self
    def HandleDiagnosticMap(dm):
      for diag in dm.values():
        if isinstance(diag, histogram_module.RelatedHistogramMap):
          diag.Resolve(histograms)

    for hist in self:
      HandleDiagnosticMap(hist.diagnostics)
      for dm in hist.nan_diagnostic_maps:
        HandleDiagnosticMap(dm)
      for hbin in hist.bins:
        for dm in hbin.diagnostic_maps:
          HandleDiagnosticMap(dm)

  def __len__(self):
    return len(self._histograms_by_guid)

  def __iter__(self):
    for hist in self._histograms_by_guid.values():
      yield hist

  def ImportDicts(self, dicts):
    if not isinstance(dicts, list):
      dicts = [dicts]
    for d in dicts:
      self.ImportDict(d)

  def ImportDict(self, dct):
    if dct.get('type') in all_diagnostics.GetDiagnosticTypenames():
      diag = diagnostic.Diagnostic.FromDict(dct)
      self._shared_diagnostics_by_guid[dct['guid']] = diag
    elif histogram_serializer.HISTOGRAMS_TAG in dct:
      for hist in histogram_deserializer.Deserialize(dct):
        self.AddHistogram(hist)
    else:
      hist = histogram_module.Histogram.FromDict(dct)
      hist.diagnostics.ResolveSharedDiagnostics(self)
      self.AddHistogram(hist)

  def AsDict(self):
    return histogram_serializer.Serialize(self)

  def ReplaceSharedDiagnostic(self, old_guid, new_diagnostic):
    if not isinstance(new_diagnostic, diagnostic_ref.DiagnosticRef):
      self._shared_diagnostics_by_guid[new_diagnostic.guid] = new_diagnostic

    old_diagnostic = self._shared_diagnostics_by_guid.get(old_guid)

    # Fast path, if they're both generic_sets, we overwrite the contents of the
    # old diagnostic.
    if isinstance(new_diagnostic, generic_set.GenericSet) and (
        isinstance(old_diagnostic, generic_set.GenericSet)):
      old_diagnostic.SetValues(list(new_diagnostic))

      self._shared_diagnostics_by_guid[new_diagnostic.guid] = old_diagnostic
      del self._shared_diagnostics_by_guid[old_guid]

      return

    for hist in self:
      for name, diag in hist.diagnostics.items():
        if diag.has_guid and diag.guid == old_guid:
          hist.diagnostics[name] = new_diagnostic
