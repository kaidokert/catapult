# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import mock

from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.api import notes
from dashboard.common import testing_common
from dashboard.models import user_note


class NotesTest(testing_common.TestCase):

  def setUp(self):
    super(NotesTest, self).setUp()
    self.SetUpApp([('/api/notes', notes.NotesHandler)])
    self.SetCurrentClientIdOAuth(api_auth.OAUTH_CLIENT_ID_WHITELIST[0])
    self.SetCurrentUserOAuth(testing_common.INTERNAL_USER)

  def _Post(self, **params):
    return json.loads(self.Post('/api/notes', params).body)

  def _CreateNote(self):
    return user_note.UserNote(
        author='internal@example.com',
        suite='a',
        measurement='b',
        bot='c',
        case='d',
        min_revision=10,
        max_revision=20,
        text='text').put()

  def testUnauthorized(self):
    self.SetCurrentUserOAuth(None)
    self.PatchObject(api_request_handler.utils, 'IsDevAppserver',
                     mock.Mock(return_value=False))
    self._CreateNote()
    result = self._Post(
        suite='a', measurement='b', bot='c', case='d', min_revision=10,
        max_revision=20)
    self.assertEqual(1, len(result))

  def testCreate(self):
    result = self._Post(
        suite='a', measurement='b', bot='c', case='d', min_revision=10,
        max_revision=20, text='text')
    self.assertEqual(1, len(result))
    self.assertEqual('a', result[0]['suite'])
    self.assertEqual('internal@example.com', result[0]['author'])
    self.assertEqual('b', result[0]['measurement'])
    self.assertEqual('c', result[0]['bot'])
    self.assertEqual('d', result[0]['case'])
    self.assertEqual(10, result[0]['min_revision'])
    self.assertEqual(20, result[0]['max_revision'])
    self.assertEqual('text', result[0]['text'])

  def testRead(self):
    key = self._CreateNote()
    result = self._Post(
        suite='a', measurement='b', bot='c', case='d', min_revision=10,
        max_revision=20)
    self.assertEqual(1, len(result))
    self.assertEqual(key.urlsafe(), result[0]['key'])
    self.assertEqual('a', result[0]['suite'])
    self.assertEqual('internal@example.com', result[0]['author'])
    self.assertEqual('b', result[0]['measurement'])
    self.assertEqual('c', result[0]['bot'])
    self.assertEqual('d', result[0]['case'])
    self.assertEqual(10, result[0]['min_revision'])
    self.assertEqual(20, result[0]['max_revision'])
    self.assertEqual('text', result[0]['text'])

  def testUpdate(self):
    key = self._CreateNote()
    result = self._Post(
        key=key.urlsafe(), suite='a', measurement='b', bot='c', case='d',
        min_revision=10, max_revision=20, text='updated')
    self.assertEqual(1, len(result))
    self.assertEqual('updated', result[0]['text'])

  def testDelete(self):
    key = self._CreateNote()
    result = self._Post(key=key.urlsafe(), text='')
    self.assertEqual(0, len(result))
    self.assertEqual(None, key.get())
