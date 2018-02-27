# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock
import unittest

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from dashboard.common import namespaced_stored_object
from dashboard.pinpoint.models import change
from dashboard.pinpoint.models import fixes


class FixesTest(unittest.TestCase):

  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()
    ndb.get_context().clear_cache()

    namespaced_stored_object.Set('repositories', {
        'chromium': {'repository_url': 'https://example.com/chromium/src'},
    })

  def tearDown(self):
    self.testbed.deactivate()

  @mock.patch.object(fixes.gitiles_service, 'CommitRange')
  def testMatch(self, commit_range):
    commit_range.return_value = [{'commit': 'a'}, {'commit': 'b'}]

    patch = change.GerritPatch('server', 'change', 'revision')
    start = change.Commit('chromium', 'start')
    end = change.Commit('chromium', 'end')
    fixes.Add(patch, start, end)

    c = change.Change((change.Commit('chromium', 'b'),))
    self.assertEqual(fixes.Get(c), patch)

  @mock.patch.object(fixes.gitiles_service, 'CommitRange')
  def testNoMatch(self, commit_range):
    commit_range.return_value = [{'commit': 'a'}, {'commit': 'b'}]

    patch = change.GerritPatch('server', 'change', 'revision')
    start = change.Commit('chromium', 'start')
    end = change.Commit('chromium', 'end')
    fixes.Add(patch, start, end)

    c = change.Change((
        change.Commit('other repository', 'a'),
        change.Commit('chromium', 'other commit'),
    ))
    self.assertIsNone(fixes.Get(c))
