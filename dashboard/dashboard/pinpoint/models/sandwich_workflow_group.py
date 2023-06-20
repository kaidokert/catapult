# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""The database model for a "SandwichWorkflowGroup"."""
from google.appengine.ext import ndb


class Workflow(ndb.Model):
  execution_name = ndb.StringProperty(indexed=True)
  execution_status = ndb.StringProperty(default='ACTIVE')


class SandwichWorkflowGroup(ndb.Model):
  name = ndb.StringProperty(indexed=True)
  bug_id = ndb.IntegerProperty()
  project = ndb.StringProperty(default='chromium')
  created = ndb.DateTimeProperty(indexed=False, auto_now_add=True)
  updated = ndb.DateTimeProperty(indexed=False, auto_now=True)
  active = ndb.BooleanProperty(indexed=True)
  workflows = ndb.StructuredProperty(Workflow, indexed=True, repeated=True)
  # TODO: add other properties that need for the final bug update/merge

  @classmethod
  def GetAll(cls, active=True):
    groups = cls.query(cls.active == active).fetch()
    return groups or []
