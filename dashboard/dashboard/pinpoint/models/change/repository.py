# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from google.appengine.ext import ndb

import logging


@ndb.transactional(propagation=ndb.TransactionOptions.INDEPENDENT)
def RepositoryUrl(name):
  """Returns the URL of a repository, given its short name.

  If a repository moved locations or has multiple locations, a repository can
  have multiple URLs. The returned URL should be the current canonical one.

  Args:
    name: The short name of the repository.

  Returns:
    A URL string, not including '.git'.
  """
  repository = ndb.Key(Repository, name).get()
  if not repository:
    raise KeyError('Unknown repository name: ' + name)
  return repository.urls[0]


def RepositoryName(url, add_if_missing=False):
  """Returns the short repository name, given its URL.

  By default, the short repository name is the last part of the URL.
  E.g. "https://chromium.googlesource.com/v8/v8": "v8"
  In some cases this is ambiguous, so the names can be manually adjusted.
  E.g. "../chromium/src": "chromium" and "../breakpad/breakpad/src": "breakpad"

  If a repository moved locations or has multiple locations, multiple URLs can
  map to the same name. This should only be done if they are exact mirrors and
  have the same git hashes.
  "https://webrtc.googlesource.com/src": "webrtc"
  "https://webrtc.googlesource.com/src/webrtc": "old_webrtc"
  "https://chromium.googlesource.com/external/webrtc/trunk/webrtc": "old_webrtc"

  Internally, all repositories are stored by short name, which always maps to
  the current canonical URL, so old URLs are automatically "upconverted".

  Args:
    url: The repository URL.
    add_if_missing: If True, also attempts to add the URL to the database with
      the default name mapping. Throws an exception if there's a name collision.

  Returns:
    The short name as a string.
  """
  if url.endswith('.git'):
    url = url[:-4]

  # http://crbug.com/1491470 - See
  # https://cloud.google.com/appengine/docs/legacy/standard/python/ndb/queries
  #
  # urls being a repeated property we need to search that any of the url values
  # are equal to the url being provided.
  repositories = Repository.query(Repository.urls.IN([url])).fetch()
  if repositories:
    return repositories[0].key.id()

  if add_if_missing:
    return _AddRepository(url)

  raise KeyError('Unknown repository URL: %s' % url)


def _AddRepository(url):
  """Add a repository URL to the database with the default name mapping.

  The default short repository name is the last part of the URL.

  Returns:
    The short repository name.
  """
  name = url.split('/')[-1]

  repo = ndb.Key(Repository, name).get()
  # http://crbug.com/1491470 - If the repository exists, this used to throw an
  # AssertionError. commit.FromDep() will call this with add_if_missing=True
  # and there's no need to terminate the Pinpoint job for the repository
  # already being present. urls is a repeated property, so this now appends the
  # url to the list of urls if not already present.
  urls = repo.urls
  if repo and url in repo.urls:
    logging.warning(
        'Attempted to add a repository that\'s already in the '
        'Datastore: %s: %s', name, url)
    return name

  Repository(id=name, urls=repo.urls.append(url)).put()
  return name


class Repository(ndb.Model):
  _use_memcache = True
  _use_cache = True
  _memcache_timeout = 60 * 60 * 24 * 7  # 7 days worth of caching.
  urls = ndb.StringProperty(repeated=True)
