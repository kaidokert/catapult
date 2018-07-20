# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Database model for page state data.

This is used for storing front-end configuration.
"""
import json

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
      if type(c) == list:
        for row in c:
          if src_path in row[0]:
            row[0] = row[0].replace(src_path, dst_path)
            changed = True
      elif type(c) == dict:
        for row in c['seriesGroups']:
          print ''
          print row
          if src_path in row[0]:
            row[0] = row[0].replace(src_path, dst_path)
            changed = True
    if changed:
      ps.value = json.dumps(r)
      ps.put()

  except Exception:  # pylint: disable=broad-except
    return

def _MigratePageStates(src_path, dst_path):
  entities, _, more = PageState.Query().fetch_page(QUERY_PAGE_LIMIT)

  for e in entities:
    _FixPageStatePaths(e, src_path, dst_path)

  if more:
    deferred.defer(_MigratePageStates, src_path, dst_path)
