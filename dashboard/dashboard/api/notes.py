# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from dashboard.models import user_note
from dashboard.api import api_request_handler


class NotesHandler(api_request_handler.ApiRequestHandler):

  def _CheckUser(self):
    pass

  def Post(self):
    suite = self.request.get('suite')
    measurement = self.request.get('measurement')
    bot = self.request.get('bot')
    case = self.request.get('case')
    min_revision = self.request.get('min_revision')
    max_revision = self.request.get('max_revision')
    text = self.request.get('text')
    notes = []

    if text:
      note_id = self.request.get('id')
      if note_id:
        note = user_note.UserNote.query(id=note_id)
      else:
        note = user_note.UserNote()
      note.suite = suite
      note.measurement = measurement
      note.text = text
      note.bot = bot
      note.case = case
      note.min_revision = min_revision
      note.max_revision = max_revision
      note.put()
      notes.append(note)
    else:
      notes.extend(user_note.UserNote.query(
          suite=suite,
          measurement=measurement,
          bot=bot,
          case=case))

    return [note.to_dict() for note in notes]
