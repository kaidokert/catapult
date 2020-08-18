# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""The datastore models for upload tokens and related data."""
from __future__ import absolute_import

from google.appengine.ext import ndb

from dashboard.models import internal_only_model

# Adding histogram in average takes about 5 minutes, so holding token in
# memory for 10 minutes should be enough.
_MEMCACHE_TIMEOUT = 60 * 10


class State(object):
  PENDING = 0
  PROCESSING = 1
  FAILED = 2
  COMPLETED = 3


class _StateModel(internal_only_model.InternalOnlyModel):
  state_ = ndb.IntegerProperty(
      name="state", default=State.PENDING, indexed=False)

  @classmethod
  def UpdateStateById(cls, model_id, state):
    if model_id is None:
      return
    obj = cls.get_by_id(model_id)
    cls.UpdateObjectState(obj, state)

  @classmethod
  def UpdateObjectState(cls, obj, state):
    if obj is None:
      return
    obj.UpdateStateAsync(state)

  @ndb.tasklet
  def UpdateStateAsync(self, state):
    self.state_ = state
    yield self.put_async()

  @property
  def state(self):
    substates_keys = getattr(self, 'substates', None)
    if not substates_keys:
      return self.state_

    # "child is None" means that it was expired and removed from memcache.
    # State of such child doesn't affect parent state.
    all_states = [
        child.state
        for child in ndb.get_multi(substates_keys)
        if child is not None
    ]
    all_states.append(self.state_)
    if all(s == State.PENDING for s in all_states):
      return State.PENDING
    if any(s in (State.PROCESSING, State.PENDING) for s in all_states):
      return State.PROCESSING
    if any(s == State.FAILED for s in all_states):
      return State.FAILED
    return State.COMPLETED


class Token(_StateModel):
  """Token is used to get state of request.

  Token can contain multiple Measurement. One per each histogram in the
  request. States of nested Measurements affect state of the Token. Created
  nested measurements have PROCESSING state.

  For now Token is stored only in memcache, therefore, there is no guarantees,
  that it won't be deleted before the request completion.
  """
  _use_memcache = True
  _use_datastore = False
  _memcache_timeout = _MEMCACHE_TIMEOUT

  internal_only = ndb.BooleanProperty(default=True)

  creation_time = ndb.DateTimeProperty(auto_now_add=True, indexed=True)

  update_time = ndb.DateTimeProperty(auto_now=True, indexed=True)

  temporary_staging_file_path = ndb.StringProperty(indexed=False, default=None)

  substates = ndb.KeyProperty(repeated=True, kind='Measurement')

  def CreateMeasurement(self, test_path):
    measurement = Measurement(state_=State.PROCESSING, id=test_path)
    measurement.put()
    self.substates.append(measurement.key)
    self.put()
    return measurement


class Measurement(_StateModel):
  """Measurement represents state of added histogram.

  Measurement are keyed by the full path to the test (for example
  master/bot/test/metric/page).

  For now Measurement is stored only in memcache, therefore, there is no
  guarantees, that it won't be deleted before the request completion.
  """
  _use_memcache = True
  _use_datastore = False
  _memcache_timeout = _MEMCACHE_TIMEOUT

  internal_only = ndb.BooleanProperty(default=True)
