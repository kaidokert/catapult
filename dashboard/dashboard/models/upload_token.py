# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""The datastore models for upload tokens and related data."""
from __future__ import absolute_import

from google.appengine.ext import ndb

from dashboard.models import internal_only_model

class UploadToken(internal_only_model.InternalOnlyModel):
  """TODO(gotthit): fill the comment

  Lorem ipsum. Lorem ipsum. Lorem ipsum. Lorem ipsum.
  """
  _use_memcache = True

  internal_only = ndb.BooleanProperty(default=True)

  temporary_staging_file_path = ndb.StringProperty(indexed=False)

  state = ndb.IntegerProperty(default=0, indexed=False)

  creation_time = ndb.DateTimeProperty(auto_now_add=True, indexed=True)

  update_time = ndb.DateTimeProperty(auto_now=True, indexed=True)
