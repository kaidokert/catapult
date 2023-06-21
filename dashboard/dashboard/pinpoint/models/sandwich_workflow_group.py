# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""The database model for a "SandwichWorkflowGroup"."""
from google.appengine.ext import ndb


class Workflow(ndb.Model):
  execution_name = ndb.StringProperty()
  execution_status = ndb.StringProperty(default='ACTIVE')
  kind = ndb.StringProperty()
  commit_dict = ndb.JsonProperty()
  values_a = ndb.FloatProperty(repeated=True)
  values_b = ndb.FloatProperty(repeated=True)


class SandwichWorkflowGroup(ndb.Model):
  bug_id = ndb.IntegerProperty()
  project = ndb.StringProperty(default='chromium')
  created = ndb.DateTimeProperty(indexed=False, auto_now_add=True)
  updated = ndb.DateTimeProperty(indexed=False, auto_now=True)
  active = ndb.BooleanProperty()
  workflows = ndb.StructuredProperty(Workflow, repeated=True)
  metric = ndb.StringProperty()
  tags = ndb.JsonProperty()
  url = ndb.StringProperty()

  @classmethod
  def GetAll(cls, active=True):
    groups = cls.query(cls.active == active).fetch()
    return groups or []
