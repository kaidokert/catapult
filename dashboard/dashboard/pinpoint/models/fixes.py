# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from google.appengine.ext import ndb

from dashboard.services import gitiles_service

from dashboard.pinpoint.models import change as change_module


def Add(patch, start, end):
  """Associates a fix with a commit range.

  All future jobs will automatically apply the fix patch to any Changes in the
  commit range.

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
  """Gets a fixed version of a Change.

  Arguments:
    change: A Change to fix.

  Returns:
    A Change with a patch applied if there is a fix for the Change. Otherwise,
    the original Change.
  """
  for commit in change.commits:
    fix = ndb.Key(Fix, commit.id_string).get()
    if not fix:
      continue

    if change.patch:
      raise NotImplementedError('Unable to apply a fix patch to a failing '
                                'commit that already has a patch.')
    return change_module.Change(change.commits, fix.patch)

  return change


class Fix(ndb.Model):

  patch = ndb.PickleProperty(required=True)
