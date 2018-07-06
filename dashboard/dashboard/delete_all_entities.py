# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine import runtime

from dashboard.common import request_handler


QUERY_PAGE_LIMIT = 1000


class DeleteAllEntitiesHandler(request_handler.RequestHandler):

  def post(self):
    DeleteAllEntities(self.request.get('kind'))


def DeleteAllEntities(kind):
  """DELETES ALL ENTITIES OF KIND |kind|.

  If there are entities remaining after the deadline, this function recurses via
  the task queue.

  Args:
    kind: Required string name of model.
  """
  if not kind:
    # Query(kind='') would delete the entire datastore.
    raise ValueError('"kind" cannot be empty')

  more = True
  cursor = None
  try:
    while more:
      keys, cursor, more = ndb.Query(kind=kind).fetch_page(
          QUERY_PAGE_LIMIT, keys_only=True, start_cursor=cursor)
      logging.info('Fetched %d keys; more=%r', len(keys), more)
      ndb.delete_multi(keys)
  except runtime.DeadlineExceededError:
    taskqueue.add(url='/delete_all_entities', params={'kind': kind})
