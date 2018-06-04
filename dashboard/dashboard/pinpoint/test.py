# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from dashboard.common import namespaced_stored_object


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

    self.testbed.setup_env(
        user_is_admin='1',
        user_email='internal@chromium.org',
        user_id='123456',
        overwrite=True)

    namespaced_stored_object.Set('repositories', {
        'catapult': {'repository_url': CATAPULT_URL},
        'chromium': {'repository_url': CHROMIUM_URL},
        'another_repo': {'repository_url': 'https://another/url'},
    })
    namespaced_stored_object.Set('repository_urls_to_names', {
        CATAPULT_URL: 'catapult',
        CHROMIUM_URL: 'chromium',
    })

  def tearDown(self):
    self.testbed.deactivate()
