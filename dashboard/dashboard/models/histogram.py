# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The datastore models for histograms and diagnostics."""

import collections
import sys

from google.appengine.ext import ndb

from dashboard.models import graph_data
from dashboard.models import internal_only_model
from tracing.value.diagnostics import diagnostic as diagnostic_module


class JsonModel(internal_only_model.InternalOnlyModel):
  # Similarly to Row, we don't need to memcache these as we don't expect to
  # access them repeatedly.
  _use_memcache = False

  data = ndb.JsonProperty(compressed=True)
  test = ndb.KeyProperty(graph_data.TestMetadata)
  internal_only = ndb.BooleanProperty(default=False, indexed=True)


class Histogram(JsonModel):
  # Needed for timeseries queries (e.g. for alerting).
  revision = ndb.IntegerProperty(indexed=True)


class SparseDiagnostic(JsonModel):
  # Need for intersecting range queries.
  name = ndb.StringProperty(indexed=False)
  start_revision = ndb.IntegerProperty(indexed=True)
  end_revision = ndb.IntegerProperty(indexed=True)

  def IsDifferent(self, rhs):
    return (diagnostic_module.Diagnostic.FromDict(self.data) !=
            diagnostic_module.Diagnostic.FromDict(rhs.data))

  @classmethod
  @ndb.synctasklet
  def GetMostRecentValuesByNames(cls, test_key, diagnostic_names):
    """Gets the data in the latests sparse diagnostics with the given
       set of diagnostic names.

    Args:
      test_key: The TestKey entity to lookup the diagnotics by
      diagnostic_names: Set of the names of the diagnostics to look up

    Returns:
      A dictionary where the keys are the given names, and the values are the
      corresponding diagnostics' values.
      None if no diagnostics are found with the given keys or type.
    """
    result = yield cls.GetMostRecentValuesByNamesAsync(
        test_key, diagnostic_names)
    raise ndb.Return(result)

  @classmethod
  @ndb.tasklet
  def GetMostRecentValuesByNamesAsync(cls, test_key, diagnostic_names):
    data_by_name = yield cls.GetMostRecentDataByNamesAsync(
        test_key, diagnostic_names)
    raise ndb.Return({name: data.get('values')
                      for name, data in data_by_name.iteritems()})

  @classmethod
  @ndb.tasklet
  def GetMostRecentDataByNamesAsync(cls, test_key, diagnostic_names):
    diagnostics = yield cls.query(
        cls.end_revision == sys.maxint,
        cls.test == test_key).fetch_async()
    data_by_name = {}
    for diagnostic in diagnostics:
      if diagnostic.name not in diagnostic_names:
        continue
      assert diagnostic.name not in data_by_name, diagnostic
      assert diagnostic.data, diagnostic
      data_by_name[diagnostic.name] = diagnostic.data
    raise ndb.Return(data_by_name)

  @staticmethod
  @ndb.tasklet
  def FixDiagnostics(test_key):
    diagnostics_for_test = yield SparseDiagnostic.query(
        SparseDiagnostic.test == test_key).fetch_async()
    diagnostics_by_name = collections.defaultdict(list)

    for d in diagnostics_for_test:
      diagnostics_by_name[d.name].append(d)

    futures = []

    for diagnostics in diagnostics_by_name.itervalues():
      sorted_diagnostics = sorted(diagnostics, key=lambda d: d.start_revision)
      unique_diagnostics = []

      # Remove any possible duplicates first.
      prev = None
      for d in sorted_diagnostics:
        if not prev:
          unique_diagnostics.append(d)
          prev = d
          continue
        if not prev.IsDifferent(d):
          futures.append(d.key.delete_async())
          continue
        unique_diagnostics.append(d)
        prev = d

      # Now fixup all the start/end revisions.
      for i in xrange(len(unique_diagnostics)):
        if i == len(unique_diagnostics) - 1:
          unique_diagnostics[i].end_revision = sys.maxint
        else:
          unique_diagnostics[i].end_revision = (
              unique_diagnostics[i+1].start_revision - 1)

      futures.extend(ndb.put_multi_async(unique_diagnostics))

    yield futures
