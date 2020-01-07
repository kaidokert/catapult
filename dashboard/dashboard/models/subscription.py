# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The database model Sheriff, for sheriff rotations."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from google.appengine.ext import ndb


class Visibility(object):
  INTERNAL_ONLY = 0
  PUBLIC = 1


class Subscription(ndb.Model):
  """
  Configuration options for alerts' subscriber. It's a mappint to the
  Subscription protobuf and should never be directly stored to datastore.
  """

  revision = ndb.StringProperty()
  name = ndb.StringProperty()
  rotation_url = ndb.StringProperty()
  notification_email = ndb.StringProperty()
  bug_labels = ndb.StringProperty(repeated=True)
  bug_components = ndb.StringProperty(repeated=True)
  bug_cc_emails = ndb.StringProperty(repeated=True)
  visibility = ndb.IntegerProperty(default=Visibility.INTERNAL_ONLY)

