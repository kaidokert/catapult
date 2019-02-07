# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock
import webtest

from dashboard.common import testing_common

from dashboard.pinpoint import dispatcher
from dashboard.pinpoint.models.change import repository


CATAPULT_URL = 'https://chromium.googlesource.com/catapult'
CHROMIUM_URL = 'https://chromium.googlesource.com/chromium/src'


class TestCase(testing_common.TestCase):

  def setUp(self):
    super(TestCase, self).setUp()
    self._SetUpTestApp()
    self._SetUpStubs()
    self._PopulateData()
    self.SetCurrentUserOAuth(testing_common.EXTERNAL_USER)

  def _SetUpTestApp(self):
    self.testapp = webtest.TestApp(dispatcher.APP)
    self.testapp.extra_environ.update({'REMOTE_ADDR': 'remote_ip'})

  def _SetUpStubs(self):
    patcher = mock.patch('dashboard.services.gitiles_service.CommitInfo')
    self.addCleanup(patcher.stop)
    self.commit_info = patcher.start()
    self.commit_info.side_effect = _CommitInfoStub

    patcher = mock.patch('dashboard.services.gitiles_service.CommitRange')
    self.addCleanup(patcher.stop)
    self.commit_range = patcher.start()
    self.commit_range.side_effect = _CommitRangeStub

    patcher = mock.patch('dashboard.services.gitiles_service.FileContents')
    self.addCleanup(patcher.stop)
    self.file_contents = patcher.start()
    self.file_contents.return_value = 'deps = {}'

    patcher = mock.patch('dashboard.services.gerrit_service.GetChange')
    self.addCleanup(patcher.stop)
    self.get_change = patcher.start()
    self.get_change.return_value = {
        '_number': 567890,
        'id': 'repo~branch~id',
        'current_revision': 'abc123',
        'project': 'project/name',
        'subject': 'Patch subject.',
        'revisions': {
            'abc123': {
                '_number': 5,
                'created': '2018-02-01 23:46:56.000000000',
                'uploader': {'email': 'author@codereview.com'},
                'fetch': {
                    'http': {
                        'url': CHROMIUM_URL,
                        'ref': 'refs/changes/90/567890/5',
                    },
                },
                'commit_with_footers': 'Subject\n\nCommit message.\n'
                                       'Change-Id: I0123456789abcdef',
            },
        },
    }

  def _PopulateData(self):
    # Add repository mappings.
    repository.Repository(id='catapult', urls=[CATAPULT_URL]).put()
    repository.Repository(id='chromium', urls=[CHROMIUM_URL]).put()
    repository.Repository(id='another_repo', urls=['https://another/url']).put()


def _CommitInfoStub(repository_url, git_hash, override=False):
  del repository_url

  if git_hash == 'HEAD':
    git_hash = 'git hash at HEAD'

  components = git_hash.split('_')
  parents = []
  if not override and len(components) > 1:
    if components[0] == 'commit':
      parent_num = int(components[1]) - 1
      parents.append('commit_' + str(parent_num))

  return {
      'author': {'email': 'author@chromium.org'},
      'commit': git_hash,
      'committer': {'time': 'Fri Jan 01 00:01:00 2018'},
      'message': 'Subject.\n\nCommit message.\n'
                 'Cr-Commit-Position: refs/heads/master@{#123456}',
      'parents': parents,
  }


def _CommitRangeStub(repository_url, first_git_hash, last_git_hash):
  if last_git_hash == 'mc_4':
    # Create a set of commits where the range includes some that were merged in
    # from a different branch (in a merge commit). The tree we're simulating
    # looks like:
    #
    #   0 <- 1 <-++ # topic-branch
    #             | (merge commit)
    #        2 <- 3 <- 4 # master
    #
    # When bisecting between 2 and 4 on master, we will eventually encounter
    # commits 0 and 1 when looking at the range. These commits could have a
    # timestamp that is much earlier in the repository and is not really
    # something the midpoint traversal should look into.
    #
    # We should then only see 3 as the Midpoint and ignore 0 and 1 since those
    # commits are not in the linear history from the tip of master.
    #
    # Note that in git, "root" commits refer to themselves as the first parent.
    #
    commit_tree = [
        {'git_hash': 'mc_4', 'parents' : ['merge_3_2_1']},
        {'git_hash': 'merge_3_2_1', 'parents' : ['commit_2', 'commit_1']},
        {'git_hash': 'commit_2', 'parents' : ['commit_2']},
        {'git_hash': 'commit_1', 'parents' : ['commit_0']},
        {'git_hash': 'commit_0', 'parents' : ['commit_0']},
    ]
    def _InfoStubWithParents(commit):
      commit_info = _CommitInfoStub(repository_url, commit['git_hash'], True)
      commit_info['parents'] = commit['parents']
      return commit_info
    return [_InfoStubWithParents(commit) for commit in commit_tree]

  first_number = int(first_git_hash.split('_')[1])
  last_number = int(last_git_hash.split('_')[1])

  return [_CommitInfoStub(repository_url, 'commit_' + str(x))
          for x in xrange(last_number, first_number, -1)]

