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

  def _PopulateData(self):
    # Add repository mappings.
    repository.Repository(id='catapult', urls=[CATAPULT_URL]).put()
    repository.Repository(id='chromium', urls=[CHROMIUM_URL]).put()
    repository.Repository(id='another_repo', urls=['https://another/url']).put()


def _CommitInfoStub(repository_url, git_hash):
  del repository_url

  if git_hash == 'HEAD':
    git_hash = 'git hash at HEAD'

  return {
      'author': {'email': 'author@chromium.org'},
      'commit': git_hash,
      'committer': {'time': 'Fri Jan 01 00:01:00 2018'},
      'message': 'Subject.\n\n'
                 'Commit message.\n'
                 'Cr-Commit-Position: refs/heads/master@{#123456}',
  }


def _CommitRangeStub(repository_url, first_git_hash, last_git_hash):
  first_number = int(first_git_hash.split()[1])
  last_number = int(last_git_hash.split()[1])
  return [_CommitInfoStub(repository_url, 'commit ' + str(x))
          for x in xrange(last_number, first_number, -1)]
