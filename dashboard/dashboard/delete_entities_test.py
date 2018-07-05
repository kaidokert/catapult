# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from google.appengine.ext import ndb

from dashboard import delete_entities
from dashboard.common import testing_common
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import page_state


class DeleteEntitiesTest(testing_common.TestCase):

  def testOnlyKind(self):
    # Only delete entities of the given kind.
    anomaly.Anomaly(id='anomaly', test=utils.TestMetadataKey(
        'master/bot/suite/measurement')).put()
    page_state.PageState(id='page_state').put()
    self.assertEqual(1, len(ndb.Query(kind='PageState').fetch(keys_only=True)))
    self.assertEqual(1, len(ndb.Query(kind='Anomaly').fetch(keys_only=True)))

    delete_entities.DeleteAllEntities('PageState')
    self.assertEqual(0, len(ndb.Query(kind='PageState').fetch(keys_only=True)))
    self.assertEqual(1, len(ndb.Query(kind='Anomaly').fetch(keys_only=True)))

  def testAll(self):
    # Delete all entites of the given kind.
    for i in xrange(10):
      page_state.PageState(id=i).put()

    delete_entities.DeleteAllEntities('PageState', limit=1)
    self.assertEqual(0, len(ndb.Query(kind='PageState').fetch(keys_only=True)))
