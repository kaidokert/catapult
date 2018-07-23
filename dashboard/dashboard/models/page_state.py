# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Database model for page state data.

This is used for storing front-end configuration.
"""
import json

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import deferred
from google.appengine.ext import ndb


QUERY_PAGE_LIMIT = 1000


class PageState(ndb.Model):
  """An entity with a single blob value where id is a hash value."""

  value = ndb.BlobProperty(indexed=False)


def _FixPageStatePaths(ps, src_path, dst_path):
  try:
    r = json.loads(ps.value)

    changed = False
    for c in r['charts']:
      if isinstance(c, list):
        for row in c:
          if src_path in row[0]:
            row[0] = row[0].replace(src_path, dst_path)
            changed = True
      elif isinstance(c, dict):
        for row in c['seriesGroups']:
          if src_path in row[0]:
            row[0] = row[0].replace(src_path, dst_path)
            changed = True
    if changed:
      ps.value = json.dumps(r)
      ps.put()

  except Exception:  # pylint: disable=broad-except
    return

def _MigratePageStatesBots(src_path, dst_path, query_cursor=None):
  """Intended for dev_console usage only in the short term and then removed."""
  if query_cursor:
    query_cursor = Cursor(urlsafe=query_cursor)
  entities, next_cursor, more = PageState.wuery(
      start_cursor=query_cursor).fetch_page(QUERY_PAGE_LIMIT)

  if more:
    deferred.defer(
        _MigratePageStatesBots, src_path, dst_path, next_cursor.urlsafe())

  for e in entities:
    _FixPageStatePaths(e, src_path, dst_path)
