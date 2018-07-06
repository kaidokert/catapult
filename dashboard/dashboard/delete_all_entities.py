# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from dashboard.common import request_handler


PATH = '/delete_all_entities'
QUERY_PAGE_LIMIT = 1000


class DeleteAllEntitiesHandler(request_handler.RequestHandler):

  def post(self):
    DeleteAllEntities(self.request.get('kind'))


def DeleteAllEntities(kind):
  """DELETES ALL ENTITIES OF KIND |kind|.

  Args:
    kind: Required string name of model.
  """
  if not kind:
    # Query(kind='') would delete the entire datastore.
    raise ValueError('"kind" cannot be empty')

  keys, _, more = ndb.Query(kind=kind).fetch_page(
      QUERY_PAGE_LIMIT, keys_only=True)
  logging.info('Fetched %d keys; more=%r', len(keys), more)
  ndb.delete_multi(keys)
  logging.info('Deleted')
  if more:
    taskqueue.add(url=PATH, params={'kind': kind})
