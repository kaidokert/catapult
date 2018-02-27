# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from google.appengine.ext import ndb

from dashboard.services import gitiles_service

from dashboard.pinpoint.models import change as change_module


def Add(patch, start, end):
  """Applies a patch across a range of commits.

  Arguments:
    patch: A Patch object that will fix the failure.
    start: A Commit object, representing the first failing commit.
    end: A Commit object, representing the first passing commit.
  """
  if start.repository != end.repository:
    raise ValueError()

  commits = gitiles_service.CommitRange(
      start.repository_url, start.git_hash, end.git_hash)
  for commit_info in commits:
    commit = change_module.Commit(start.repository, commit_info['commit'])
    Fix(patch=patch, id=commit.id_string).put()


def Get(change):
  for commit in change.commits:
    fix = ndb.Key(Fix, commit.id_string).get()
    if fix:
      return fix.patch
  return None


class Fix(ndb.Model):

  patch = ndb.PickleProperty(required=True)
