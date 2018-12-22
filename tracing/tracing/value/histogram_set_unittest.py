# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from tracing.value import histogram
from tracing.value import histogram_set
from tracing.value.diagnostics import date_range
from tracing.value.diagnostics import diagnostic_ref
from tracing.value.diagnostics import generic_set

class HistogramSetUnittest(unittest.TestCase):

  def testRelatedHistogramMap(self):
    a = histogram.Histogram('a', 'unitless')
    b = histogram.Histogram('b', 'unitless')
    c = histogram.Histogram('c', 'unitless')
    rhm = histogram.RelatedHistogramMap()
    rhm.Set('y', b)
    rhm.Set('z', c)
    a.diagnostics['rhm'] = rhm

    # Don't serialize c yet.
    hists = histogram_set.HistogramSet([a, b])
    hists2 = histogram_set.HistogramSet()
    hists2.ImportDicts(hists.AsDict())
    hists2.ResolveRelatedHistograms()
    a2 = hists2.GetHistogramsNamed('a')
    self.assertEqual(len(a2), 1)
    a2 = a2[0]
    self.assertEqual(a2.guid, a.guid)
    self.assertIsInstance(a2, histogram.Histogram)
    self.assertIsNot(a2, a)
    b2 = hists2.GetHistogramsNamed('b')
    self.assertEqual(len(b2), 1)
    b2 = b2[0]
    self.assertEqual(b2.guid, b.guid)
    self.assertIsInstance(b2, histogram.Histogram)
    self.assertIsNot(b2, b)
    rhm2 = a2.diagnostics['rhm']
    self.assertIsInstance(rhm2, histogram.RelatedHistogramMap)
    self.assertEqual(len(rhm2), 2)

    # Assert that b and c are in a2's RelatedHistogramMap, rhm2.
    self.assertIs(b2, rhm2.Get('y'))
    self.assertIsInstance(rhm2.Get('z'), histogram.HistogramRef)

    # Now serialize c and add it to hists2.
    hists2.ImportDicts(histogram_set.HistogramSet([c]).AsDict())
    hists2.ResolveRelatedHistograms()

    c2 = hists2.GetHistogramsNamed('c')
    self.assertEqual(len(c2), 1)
    c2 = c2[0]
    self.assertEqual(c2.guid, c.guid)
    self.assertIsNot(c2, c)

    self.assertIs(b2, rhm2.Get('y'))
    self.assertIs(c2, rhm2.Get('z'))

  def testGetSharedDiagnosticsOfType(self):
    d0 = generic_set.GenericSet(['foo'])
    d1 = date_range.DateRange(0)
    hs = histogram_set.HistogramSet()
    hs.AddSharedDiagnosticToAllHistograms('generic', d0)
    hs.AddSharedDiagnosticToAllHistograms('generic', d1)
    diagnostics = hs.GetSharedDiagnosticsOfType(generic_set.GenericSet)
    self.assertEqual(len(diagnostics), 1)
    self.assertIsInstance(diagnostics[0], generic_set.GenericSet)

  def testImportDicts(self):
    hist = histogram.Histogram('', 'unitless')
    hists = histogram_set.HistogramSet([hist])
    hists2 = histogram_set.HistogramSet()
    hists2.ImportDicts(hists.AsDict())
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

  def testFilterHistogram(self):
    a = histogram.Histogram('a', 'unitless')
    b = histogram.Histogram('b', 'unitless')
    c = histogram.Histogram('c', 'unitless')
    hs = histogram_set.HistogramSet([a, b, c])
    hs.FilterHistograms(lambda h: h.name == 'b')

    names = set(['a', 'c'])
    for h in hs:
      self.assertIn(h.name, names)
      names.remove(h.name)
    self.assertEqual(0, len(names))

  def testRemoveOrphanedDiagnostics(self):
    da = generic_set.GenericSet(['a'])
    db = generic_set.GenericSet(['b'])
    a = histogram.Histogram('a', 'unitless')
    b = histogram.Histogram('b', 'unitless')
    hs = histogram_set.HistogramSet([a])
    hs.AddSharedDiagnosticToAllHistograms('a', da)
    hs.AddHistogram(b)
    hs.AddSharedDiagnosticToAllHistograms('b', db)
    hs.FilterHistograms(lambda h: h.name == 'a')

    dicts = hs.AsDict()
    self.assertEqual(3, len(dicts))

    hs.RemoveOrphanedDiagnostics()
    dicts = hs.AsDict()
    self.assertEqual(2, len(dicts))

  def testAddSharedDiagnostic(self):
    diags = {}
    da = generic_set.GenericSet(['a'])
    db = generic_set.GenericSet(['b'])
    diags['da'] = da
    diags['db'] = db
    a = histogram.Histogram('a', 'unitless')
    b = histogram.Histogram('b', 'unitless')
    hs = histogram_set.HistogramSet()
    hs.AddSharedDiagnostic(da)
    hs.AddHistogram(a, {'da': da})
    hs.AddHistogram(b, {'db': db})

    # This should produce one shared diagnostic and 2 histograms.
    dicts = hs.AsDict()
    self.assertEqual(3, len(dicts))
    self.assertEqual(da.AsDict(), dicts[0])


    # Assert that you only see the shared diagnostic once.
    seen_once = False
    for idx, val in enumerate(dicts):
      if idx == 0:
        continue
      if 'da' in val['diagnostics']:
        self.assertFalse(seen_once)
        self.assertEqual(val['diagnostics']['da'], da.guid)
        seen_once = True


  def testSharedDiagnostic(self):
    hist = histogram.Histogram('', 'unitless')
    hists = histogram_set.HistogramSet([hist])
    diag = generic_set.GenericSet(['shared'])
    hists.AddSharedDiagnosticToAllHistograms('generic', diag)

    # Serializing a single Histogram with a single shared diagnostic should
    # produce 2 dicts.
    ds = hists.AsDict()
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

    self.assertIsInstance(
        hist2.diagnostics.get('generic'), generic_set.GenericSet)
    self.assertEqual(list(diag), list(hist2.diagnostics.get('generic')))

  def testReplaceSharedDiagnostic(self):
    hist = histogram.Histogram('', 'unitless')
    hists = histogram_set.HistogramSet([hist])
    diag0 = generic_set.GenericSet(['shared0'])
    diag1 = generic_set.GenericSet(['shared1'])
    hists.AddSharedDiagnosticToAllHistograms('generic0', diag0)
    hists.AddSharedDiagnosticToAllHistograms('generic1', diag1)

    guid0 = diag0.guid
    guid1 = diag1.guid

    hists.ReplaceSharedDiagnostic(
        guid0, diagnostic_ref.DiagnosticRef('fakeGuid'))

    self.assertEqual(hist.diagnostics['generic0'].guid, 'fakeGuid')
    self.assertEqual(hist.diagnostics['generic1'].guid, guid1)

  def testReplaceSharedDiagnostic_NonRefAddsToMap(self):
    hist = histogram.Histogram('', 'unitless')
    hists = histogram_set.HistogramSet([hist])
    diag0 = generic_set.GenericSet(['shared0'])
    diag1 = generic_set.GenericSet(['shared1'])
    hists.AddSharedDiagnosticToAllHistograms('generic0', diag0)

    guid0 = diag0.guid
    guid1 = diag1.guid

    hists.ReplaceSharedDiagnostic(guid0, diag1)

    self.assertIsNotNone(hists.LookupDiagnostic(guid1))
