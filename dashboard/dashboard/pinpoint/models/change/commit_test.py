# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import mock

from dashboard.pinpoint.models.change import commit
from dashboard.pinpoint import test


COMMIT_A = commit.Commit('chromium', '0e57e2b')
COMMIT_B = commit.Commit('chromium', 'babe852')
COMMIT_MIDPOINT = commit.Commit('chromium', '949b36d')


@contextlib.contextmanager
def SetMidpoint():
  patcher = mock.patch.object(commit.gitiles_service, 'CommitRange')
  patcher.start().return_value = [
      {'commit': 'babe852'},
      {'commit': 'b57345e'},
      {'commit': '949b36d'},
      {'commit': '1ef4789'},
  ]
  yield
  patcher.stop()


class CommitTest(test.TestCase):

  def testCommit(self):
    c = commit.Commit('chromium', 'aaa7336c821888839f759c6c0a36')

    other_commit = commit.Commit(u'chromium', u'aaa7336c821888839f759c6c0a36')
    self.assertEqual(c, other_commit)
    self.assertEqual(str(c), 'chromium@aaa7336')
    self.assertEqual(c.id_string, 'chromium@aaa7336c821888839f759c6c0a36')
    self.assertEqual(c.repository, 'chromium')
    self.assertEqual(c.git_hash, 'aaa7336c821888839f759c6c0a36')
    self.assertEqual(c.repository_url, test.CHROMIUM_URL)

  @mock.patch('dashboard.services.gitiles_service.FileContents')
  def testDeps(self, file_contents):
    file_contents.return_value = """
vars = {
  'chromium_git': 'https://chromium.googlesource.com',
  'webrtc_git': 'https://webrtc.googlesource.com',
  'webrtc_rev': 'deadbeef',
}
deps = {
  'src/v8': Var('chromium_git') + '/v8/v8.git' + '@' + 'c092edb',
  'src/third_party/lighttpd': {
    'url': Var('chromium_git') + '/deps/lighttpd.git' + '@' + '9dfa55d',
    'condition': 'checkout_mac or checkout_win',
  },
  'src/third_party/webrtc': {
    'url': '{webrtc_git}/src.git',
    'revision': '{webrtc_rev}',
  },
  'src/third_party/intellij': {
    'packages': [{
      'package': 'chromium/third_party/intellij',
      'version': 'version:12.0-cr0',
    }],
    'condition': 'checkout_android',
    'dep_type': 'cipd',
  },
}
deps_os = {
  'win': {
    'src/third_party/cygwin':
      Var('chromium_git') + '/chromium/deps/cygwin.git' + '@' + 'c89e446',
  }
}
    """

    expected = frozenset((
        ('https://chromium.googlesource.com/chromium/deps/cygwin', 'c89e446'),
        ('https://chromium.googlesource.com/deps/lighttpd', '9dfa55d'),
        ('https://chromium.googlesource.com/v8/v8', 'c092edb'),
        ('https://webrtc.googlesource.com/src', 'deadbeef'),
    ))
    self.assertEqual(COMMIT_A.Deps(), expected)

  def testAsDict(self):
    self.commit_info.side_effect = None
    self.commit_info.return_value = {
        'author': {'email': 'author@chromium.org'},
        'commit': 'aaa7336',
        'committer': {'time': 'Fri Jan 01 00:01:00 2016'},
        'message': 'Subject.\n\n'
                   'Commit message.\n'
                   'Cr-Commit-Position: refs/heads/master@{#437745}',
    }

    expected = {
        'repository': 'chromium',
        'git_hash': 'aaa7336',
        'url': test.CHROMIUM_URL + '/+/aaa7336',
        'subject': 'Subject.',
        'author': 'author@chromium.org',
        'time': 'Fri Jan 01 00:01:00 2016',
        'commit_position': 437745,
    }
    self.assertEqual(COMMIT_A.AsDict(), expected)

  def testFromDepNewRepo(self):
    c = commit.Commit.FromDep(commit.Dep('https://new/repository/url.git', 'git_hash'))
    self.assertEqual(c, commit.Commit('url', 'git_hash'))

  def testFromDepExistingRepo(self):
    c = commit.Commit.FromDep(commit.Dep(test.CHROMIUM_URL, '0e57e2b'))
    self.assertEqual(c, COMMIT_A)

  def testFromDict(self):
    c = commit.Commit.FromDict({
        'repository': 'chromium',
        'git_hash': '0e57e2b',
    })
    self.assertEqual(c, COMMIT_A)

  def testFromDictWithRepositoryUrl(self):
    c = commit.Commit.FromDict({
        'repository': test.CHROMIUM_URL,
        'git_hash': '0e57e2b',
    })
    self.assertEqual(c, COMMIT_A)

  def testFromDictResolvesHEAD(self):
    c = commit.Commit.FromDict({
        'repository': test.CHROMIUM_URL,
        'git_hash': 'HEAD',
    })

    expected = commit.Commit('chromium', 'git hash at HEAD')
    self.assertEqual(c, expected)

  def testFromDictFailureFromUnknownRepo(self):
    with self.assertRaises(KeyError):
      commit.Commit.FromDict({
          'repository': 'unknown repo',
          'git_hash': 'git hash',
      })

  def testFromDictFailureFromUnknownCommit(self):
    self.commit_info.side_effect = KeyError()

    with self.assertRaises(KeyError):
      commit.Commit.FromDict({
          'repository': 'chromium',
          'git_hash': 'unknown git hash',
      })


class MidpointTest(test.TestCase):

  def testSuccess(self):
    with SetMidpoint():
      midpoint = commit.Commit.Midpoint(COMMIT_A, COMMIT_B)
    self.assertEqual(midpoint, COMMIT_MIDPOINT)

  def testSameCommit(self):
    midpoint = commit.Commit.Midpoint(COMMIT_A, COMMIT_A)
    self.assertEqual(midpoint, COMMIT_A)

  def testAdjacentCommits(self):
    midpoint = commit.Commit.Midpoint(COMMIT_A, COMMIT_B)
    self.assertEqual(midpoint, COMMIT_A)

  def testRaisesWithDifferingRepositories(self):
    commit_b = commit.Commit('not_chromium', 'babe852')
    with self.assertRaises(commit.NonLinearError):
      commit.Commit.Midpoint(COMMIT_A, commit_b)

  @mock.patch('dashboard.services.gitiles_service.CommitRange')
  def testRaisesWithEmptyRange(self, commit_range):
    commit_range.return_value = []

    with self.assertRaises(commit.NonLinearError):
      commit.Commit.Midpoint(COMMIT_A, COMMIT_B)
