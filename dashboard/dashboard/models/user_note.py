# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from google.appengine.ext import ndb

class UserNote(ndb.Model):
  suite = ndb.StringProperty()
  measurement = ndb.StringProperty()
  bot = ndb.StringProperty()
  case = ndb.StringProperty()
  text = ndb.TextProperty()
  min_revision = ndb.IntegerProperty()
  max_revision = ndb.IntegerProperty()
