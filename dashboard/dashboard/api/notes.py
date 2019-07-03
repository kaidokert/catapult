# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from google.appengine.ext import ndb

from dashboard.api import api_request_handler
from dashboard.common import utils
from dashboard.models import user_note


class NotesHandler(api_request_handler.ApiRequestHandler):

  def _CheckUser(self):
    self._CheckIsLoggedIn()

  def Post(self):
    suite = self.request.get('suite')
    measurement = self.request.get('measurement')
    bot = self.request.get('bot')
    case = self.request.get('case')
    min_revision = self.request.get('min_revision', None)
    max_revision = self.request.get('max_revision', None)
    text = self.request.get('text', None)
    key = self.request.get('key')
    limit = int(self.request.get('limit', 1000))

    if min_revision is not None:
      if min_revision.isdigit():
        min_revision = int(min_revision)
      else:
        min_revision = None
    if max_revision is not None:
      if max_revision.isdigit():
        max_revision = int(max_revision)
      else:
        max_revision = None

    notes = []

    if text is None:
      # Query for notes
      query = user_note.UserNote.query(
          user_note.UserNote.suite == suite,
          user_note.UserNote.measurement == measurement,
          user_note.UserNote.bot == bot,
          user_note.UserNote.case == case)

      if max_revision:
        query = query.filter(user_note.UserNote.min_revision < max_revision)
        # TODO index

      # TODO fetch_page, cursor
      for note in query.fetch(limit):
        if min_revision is None or note.max_revision > min_revision:
          notes.append(note)
    else:
      # The user is creating, editing, or deleting a note.
      note = None
      if key:
        # The user is trying to edit or delete a note.
        note = ndb.Key(urlsafe=key).get()
        if note:
          if note.author != utils.GetEmail():
            raise api_request_handler.ForbiddenError()

          if text == '':
            # Delete the note.
            note.key.delete()

      if text:
        if note is None:
          # Create a new UserNote.
          note = user_note.UserNote()
          note.author = utils.GetEmail()

        note.suite = suite
        note.measurement = measurement
        note.bot = bot
        note.case = case
        note.min_revision = min_revision
        note.max_revision = max_revision

        note.text = text

        note.put()
        notes.append(note)

    dicts = []
    for note in notes:
      d = note.to_dict()
      d['key'] = note.key.urlsafe()
      d['updated'] = note.updated.isoformat()
      dicts.append(d)
    return dicts
