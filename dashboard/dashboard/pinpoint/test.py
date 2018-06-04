# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from dashboard.pinpoint.models.change import repository


CATAPULT_URL = 'https://chromium.googlesource.com/catapult'
CHROMIUM_URL = 'https://chromium.googlesource.com/chromium/src'


class TestCase(unittest.TestCase):

  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()
    ndb.get_context().clear_cache()
    self.testbed.init_user_stub()
    root_path = os.path.join(os.path.dirname(__file__), '..', '..')
    self.testbed.init_taskqueue_stub(root_path=root_path)

    repository.Repository(id='catapult', urls=[CATAPULT_URL]).put()
    repository.Repository(id='chromium', urls=[CHROMIUM_URL]).put()
    repository.Repository(id='another_repo', urls=['https://another/url']).put()

  def tearDown(self):
    self.testbed.deactivate()
