# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import time

from google.appengine.ext import ndb


def DeleteAllEntities(kind, limit=5000, deadline_seconds=50):
  """DELETES ALL ENTITIES OF KIND |kind|.

  This function is intended to be called in the dev console.

  Args:
    kind: String name of model.
    limit: Number of keys to fetch in each page.
    deadline_seconds: Number of seconds to stop after.

  Returns:
    more: True if there might be more entities that could not be deleted within
    |deadline_seconds|.
  """
  more = True
  cursor = None
  deadline = time.time() + deadline_seconds
  while more and time.time() < deadline:
    query = ndb.Query(kind=kind)
    # Let's keep things synchronous for simplicity.
    keys, cursor, more = query.fetch_page(
        limit, keys_only=True, start_cursor=cursor)
    logging.info('Fetched %d keys; more=%r', len(keys), more)
    ndb.delete_multi(keys)
  return more
