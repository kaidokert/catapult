# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from tracing.value import histogram
from tracing.value import histogram_set
from tracing.value.diagnostics import diagnostic_ref


class HistogramSetUnittest(unittest.TestCase):

  def testGetSharedDiagnosticsOfType(self):
    d0 = histogram.GenericSet(['foo'])
    d1 = histogram.DateRange(0)
    hs = histogram_set.HistogramSet()
    hs.AddSharedDiagnostic('generic', d0)
    hs.AddSharedDiagnostic('generic', d1)
    diagnostics = hs.GetSharedDiagnosticsOfType(histogram.GenericSet)
    self.assertEqual(len(diagnostics), 1)
    self.assertIsInstance(diagnostics[0], histogram.GenericSet)

  def testImportDicts(self):
    hist = histogram.Histogram('', 'unitless')
    hists = histogram_set.HistogramSet([hist])
    hists2 = histogram_set.HistogramSet()
    hists2.ImportDicts(hists.AsDicts())
    self.assertEqual(len(hists), len(hists2))

  def testAddHistogramRaises(self):
    hist = histogram.Histogram('', 'unitless')
    hists = histogram_set.HistogramSet([hist])
    with self.assertRaises(Exception):
      hists.AddHistogram(hist)
    hist2 = histogram.Histogram('', 'unitless')
    # Do not ever do this in real code:
    hist2.guid = hist.guid
    with self.assertRaises(Exception):
      hists.AddHistogram(hist2)

  def testSharedDiagnostic(self):
    hist = histogram.Histogram('', 'unitless')
    hists = histogram_set.HistogramSet([hist])
    diag = histogram.GenericSet(['shared'])
    hists.AddSharedDiagnostic('generic', diag)

    # Serializing a single Histogram with a single shared diagnostic should
    # produce 2 dicts.
    ds = hists.AsDicts()
    self.assertEqual(len(ds), 2)
    self.assertEqual(diag.AsDict(), ds[0])

    # The serialized Histogram should refer to the shared diagnostic by its
    # guid.
    self.assertEqual(ds[1]['diagnostics']['generic'], diag.guid)

    # Deserialize ds.
    hists2 = histogram_set.HistogramSet()
    hists2.ImportDicts(ds)
    self.assertEqual(len(hists2), 1)
    hist2 = [h for h in hists2][0]

    # The diagnostic reference should be deserialized as a DiagnosticRef until
    # resolveRelatedHistograms is called.
    self.assertIsInstance(
        hist2.diagnostics.get('generic'), diagnostic_ref.DiagnosticRef)
    hists2.ResolveRelatedHistograms()
    self.assertIsInstance(
        hist2.diagnostics.get('generic'), histogram.GenericSet)
    self.assertEqual(list(diag), list(hist2.diagnostics.get('generic')))

  def testReplaceSharedDiagnostic(self):
    hist = histogram.Histogram('', 'unitless')
    hists = histogram_set.HistogramSet([hist])
    diag0 = histogram.GenericSet(['shared0'])
    diag1 = histogram.GenericSet(['shared1'])
    hists.AddSharedDiagnostic('generic0', diag0)
    hists.AddSharedDiagnostic('generic1', diag1)

    guid0 = diag0.guid
    guid1 = diag1.guid

    hists.ReplaceSharedDiagnostic(
        guid0, diagnostic_ref.DiagnosticRef('fakeGuid'))

    self.assertEqual(hist.diagnostics['generic0'].guid, 'fakeGuid')
    self.assertEqual(hist.diagnostics['generic1'].guid, guid1)

  def testReplaceSharedDiagnostic_NonRefAddsToMap(self):
    hist = histogram.Histogram('', 'unitless')
    hists = histogram_set.HistogramSet([hist])
    diag0 = histogram.GenericSet(['shared0'])
    diag1 = histogram.GenericSet(['shared1'])
    hists.AddSharedDiagnostic('generic0', diag0)

    guid0 = diag0.guid
    guid1 = diag1.guid

    hists.ReplaceSharedDiagnostic(guid0, diag1)

    self.assertIsNotNone(hists.LookupDiagnostic(guid1))
