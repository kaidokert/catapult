# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The datastore models for histograms and diagnostics."""

import collections
import json
import sys

from google.appengine.ext import ndb

from dashboard.common import utils
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

  @staticmethod
  @ndb.synctasklet
  def GetMostRecentValuesByNames(test_key, diagnostic_names):
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
    result = yield SparseDiagnostic.GetMostRecentValuesByNamesAsync(
        test_key, diagnostic_names)
    raise ndb.Return(result)

  @staticmethod
  @ndb.tasklet
  def GetMostRecentValuesByNamesAsync(test_key, diagnostic_names):
    diagnostics = yield SparseDiagnostic.query(
        ndb.AND(SparseDiagnostic.end_revision == sys.maxint,
                SparseDiagnostic.test == test_key)).fetch_async()

    diagnostic_map = {}

    for diagnostic in diagnostics:
      if diagnostic.name in diagnostic_names:
        assert diagnostic_map.get(diagnostic.name) is None
        diagnostic_data = json.loads(diagnostic.data)
        diagnostic_map[diagnostic.name] = diagnostic_data.get('values')
    raise ndb.Return(diagnostic_map)

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

  @staticmethod
  @ndb.tasklet
  def FindOrInsertDiagnostics(new_entities, test, rev, last_rev):
    if rev >= last_rev:
      # If this is the latest commit, we can go through usual path of checking
      # if the diagnostic changed and updating the previous one.
      results = yield _FindOrInsertDiagnosticsLast(new_entities, test, rev)
    else:
      # This came in out of order, so add the diagnostic as a singular point and
      # then fixup all diagnostics.
      results = yield _FindOrInsertDiagnosticsOutOfOrder(
          new_entities, test, rev)
    raise ndb.Return(results)


@ndb.tasklet
def _FindOrInsertDiagnosticsLast(new_entities, test, rev):
  print
  print new_entities

  query = SparseDiagnostic.query(
      ndb.AND(
          SparseDiagnostic.end_revision == sys.maxint,
          SparseDiagnostic.test == test))
  diagnostic_entities = yield query.fetch_async()
  diagnostic_entities = dict((d.name, d) for d in diagnostic_entities)
  entity_futures = []
  new_guids_to_existing_diagnostics = {}

  for new_entity in new_entities:
    old_entity = diagnostic_entities.get(new_entity.name)
    if old_entity is not None:
      # Case 1: One in datastore, different from new one.
      if old_entity.IsDifferent(new_entity):
        old_entity.end_revision = rev - 1
        entity_futures.append(old_entity.put_async())
        new_entity.start_revision = rev
        new_entity.end_revision = sys.maxint
        entity_futures.append(new_entity.put_async())
      # Case 2: One in datastore, same as new one.
      else:
        new_guids_to_existing_diagnostics[new_entity.key.id()] = old_entity.data
      continue
    # Case 3: Nothing in datastore.
    entity_futures.append(new_entity.put_async())

  yield entity_futures
  raise ndb.Return(new_guids_to_existing_diagnostics)


@ndb.tasklet
def _FindNextRevision(test_key, rev):
  test_key = utils.OldStyleTestKey(test_key)
  q = graph_data.Row.query(
      graph_data.Row.parent_test == test_key, graph_data.Row.revision > rev)
  q = q.order(graph_data.Row.revision)
  rows = yield q.fetch_async(limit=1)
  if rows:
    raise ndb.Return(rows[0].revision - 1)
  raise ndb.Return(sys.maxint)


@ndb.tasklet
def _FindOrInsertNamedDiagnosticsOutOfOrder(
    new_diagnostic, old_diagnostics, rev):
  print
  print '_FindOrInsertNamedDiagnosticsOutOfOrder'
  print old_diagnostics
  print
  print new_diagnostic
  print
  for i in xrange(len(old_diagnostics)):
    cur = old_diagnostics[i]

    # Overall there are 2 major cases to handle. Either you're clobbering an
    # existing diagnostic by uploading right to the start of that diagnostic's
    # range, or you're splitting the range.
    #
    # We treat insertions by assuming that the new diagnostic is valid until the
    # next uploaded commit, since that commit will have had a diagnostic on it
    # which will have been diffed and inserted appropriately at the time.

    # Case 1, clobber the existing diagnostic.
    if rev == cur.start_revision:
      if not cur.IsDifferent(new_diagnostic):
        break

      next_diag = None
      if i > 0:
        next_diag = old_diagnostics[i-1]

      next_revision = yield _FindNextRevision(cur.test, rev)

      # There's 2 cases to handle, either there's another diagnostic range
      # after this, or there isn't.

      # If there is another diagnostic, we split and create a new diagnostic
      # for the latter half, between [next_revision + 1, next_diagnostic]
      # There's an additional check to make sure there's even room to do that.
      if next_diag and (next_diag.start_revision - 1) != next_revision:
        clone = SparseDiagnostic(
            data=cur.data, test=cur.test,
            start_revision=next_revision + 1, end_revision=cur.end_revision,
            name=cur.name, internal_only=cur.internal_only)
        yield clone.put_async()

      # If there isn't, we need to split the range and create a new diagnostic
      # for the latter half, between [next_revision + 1, infinity]
      elif not next_diag and next_revision != sys.maxint:
        clone = SparseDiagnostic(
            data=cur.data, test=cur.test,
            start_revision=next_revision + 1, end_revision=cur.end_revision,
            name=cur.name, internal_only=cur.internal_only)
        yield clone.put_async()
      cur.data = new_diagnostic.data
      cur.end = next_revision
      yield cur.put_async()
      break

    # Case 2, split the range.
    elif rev > cur.start_revision and rev <= cur.end_revision:
      if not cur.IsDifferent(new_diagnostic):
        break

      next_diag = None
      if i > 0:
        next_diag = old_diagnostics[i-1]

      next_revision = yield _FindNextRevision(cur.test, rev)

      cur.end_revision = rev - 1
      new_diagnostic.start_revision = rev
      new_diagnostic.end_revision = next_revision

      # When splitting the range, need to check if there's enough room to make
      # another range before the next one.
      if next_diag and (next_diag.start_revision - 1) != next_revision:
        clone = SparseDiagnostic(
            data=cur.data, test=cur.test,
            start_revision=next_revision + 1, end_revision=cur.end_revision,
            name=cur.name, internal_only=cur.internal_only)
        yield clone.put_async()
      yield (cur.put_async(), new_diagnostic.put_async())
      break


@ndb.tasklet
def _FindOrInsertDiagnosticsOutOfOrder(new_entities, test, rev):
  query = SparseDiagnostic.query(
      ndb.AND(
          SparseDiagnostic.end_revision >= rev,
          SparseDiagnostic.test == test))
  query = query.order(-SparseDiagnostic.end_revision)
  diagnostic_entities = yield query.fetch_async()

  new_entities_by_name = dict((d.name, d) for d in new_entities)
  diagnostics_by_name = collections.defaultdict(list)

  for d in diagnostic_entities:
    diagnostics_by_name[d.name].append(d)

  futures = []

  for name in diagnostics_by_name.iterkeys():
    if not name in new_entities_by_name:
      continue

    futures.append(
        _FindOrInsertNamedDiagnosticsOutOfOrder(
            new_entities_by_name[name], diagnostics_by_name[name], rev))

  yield futures

  # This was before any existing diagnostic, so just run a full cleanup pass.
  if new_entities_by_name:
    yield ndb.put_multi_async(new_entities_by_name.itervalues())
    yield SparseDiagnostic.FixDiagnostics(test)

  raise ndb.Return({})
