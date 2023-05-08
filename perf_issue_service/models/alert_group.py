# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from google.cloud import ndb


class NoEntityFoundException(Exception):
  pass

class BugInfo(ndb.Model):
  project = ndb.StringProperty(indexed=True)
  bug_id = ndb.IntegerProperty(indexed=True)

class AlertGroup(ndb.Model):
  name = ndb.StringProperty(indexed=True)
  domain = ndb.StringProperty(indexed=True)
  subscription_name = ndb.StringProperty(indexed=True)
  created = ndb.DateTimeProperty(indexed=False, auto_now_add=True)
  updated = ndb.DateTimeProperty(indexed=False, auto_now_add=True)

  class Status:
    unknown = 0
    untriaged = 1
    triaged = 2
    bisected = 3
    closed = 4

  status = ndb.IntegerProperty(indexed=False)

  class Type:
    test_suite = 0
    logical = 1
    reserved = 2

  group_type = ndb.IntegerProperty(
      indexed=False,
      choices=[Type.test_suite, Type.logical, Type.reserved],
      default=Type.test_suite,
  )
  active = ndb.BooleanProperty(indexed=True)
#   revision = ndb.LocalStructuredProperty(RevisionRange)
  bug = ndb.StructuredProperty(BugInfo, indexed=True)
  project_id = ndb.StringProperty(indexed=True, default='chromium')
  bisection_ids = ndb.StringProperty(repeated=True)
  anomalies = ndb.KeyProperty(repeated=True)
  # Key of canonical AlertGroup. If not None the group is considered to be
  # duplicate.
  canonical_group = ndb.KeyProperty(indexed=True)

  @classmethod
  def FindDuplicates(cls, group_id):
    client = ndb.Client()
    with client.context():
      query = cls.query(
          cls.active == True,
          cls.canonical_group == ndb.Key('AlertGroup', group_id))
      duplicates = query.fetch()
      return [g.key.string_id() for g in duplicates]


  @classmethod
  def FindCanonicalGroupByIssue(cls, issue_id, project_name):
    client = ndb.Client()
    with client.context():
      query = cls.query(
          cls.active == True,
          cls.bug.project == project_name,
          cls.bug.bug_id == issue_id)
      query_result = query.fetch(limit=1)
      if not query_result:
        return None

      canonical_group = query_result[0]
      visited = set()
      while canonical_group.canonical_group:
        visited.add(canonical_group.key)
        next_group_key = canonical_group.canonical_group
        # Visited check is just precaution.
        # If it is true - the system previously failed to prevent loop creation.
        if next_group_key == self._group.key or next_group_key in visited:
          logging.warning(
              'Alert group auto merge failed. Found a loop while '
              'searching for a canonical group for %r', self._group)
          return None
        canonical_group = next_group_key.get()
      
      return canonical_group.key.string_id()


  @classmethod
  def GetAnomaliesByID(cls, group_id):
    """ Given a group id, return a list of anomaly id.
    """
    client = ndb.Client()
    with client.context():
      group = ndb.Key('AlertGroup', group_id).get()
      if group:
        return [a.integer_id() for a in group.anomalies]
      raise NoEntityFoundException('No Alert Group Found with id: %s', group_id)
