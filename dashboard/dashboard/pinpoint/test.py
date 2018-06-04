# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest

import webtest

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from dashboard.pinpoint import dispatcher
from dashboard.pinpoint.models.change import repository


CATAPULT_URL = 'https://chromium.googlesource.com/catapult'
CHROMIUM_URL = 'https://chromium.googlesource.com/chromium/src'


_ROOT_PATH = os.path.join(os.path.dirname(__file__), '..', '..')


class TestCase(unittest.TestCase):

  def setUp(self):
    self._SetUpTestbed()
    self._SetUpTestApp()
    self._PopulateData()

  def _SetUpTestbed(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.addCleanup(self.testbed.deactivate)

    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()
    self.testbed.init_taskqueue_stub(root_path=_ROOT_PATH)
    self.testbed.init_user_stub()

    ndb.get_context().clear_cache()

  def _SetUpTestApp(self):
    self.testapp = webtest.TestApp(dispatcher.APP)
    self.testapp.extra_environ.update({'REMOTE_ADDR': 'remote_ip'})

  def _PopulateData(self):
    # Add repository mappings.
    repository.Repository(id='catapult', urls=[CATAPULT_URL]).put()
    repository.Repository(id='chromium', urls=[CHROMIUM_URL]).put()
    repository.Repository(id='another_repo', urls=['https://another/url']).put()

  def GetTaskQueueTasks(self, task_queue_name):
    task_queue = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
    return task_queue.GetTasks(task_queue_name)
