# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json

from dashboard.pinpoint import test
from dashboard.pinpoint.handlers import deps


class DepsTest(test.TestCase):

  def testGet_OK(self):
    self.file_contents.return_value = """
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
    'url': '{webrtc_git}/src.git@{webrtc_rev}',
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
    """

    # The response should be sorted.
    expected = [
        ['https://chromium.googlesource.com/deps/lighttpd', '9dfa55d'],
        ['https://chromium.googlesource.com/v8/v8', 'c092edb'],
        ['https://webrtc.googlesource.com/src', 'deadbeef'],
    ]
    expected.sort()

    url = '/api/deps?repository_url=' + test.CHROMIUM_URL + '&git_hash=bar'

    resp = self.testapp.get(url)
    data = json.loads(resp.body)

    self.assertEqual(resp.status, 200)
    self.assertEqual(data, expected)

  def testGet_RequiredKeys(self):
    # Missing repository_url
    url = '/api/deps&git_hash=bar'
    resp = self.testapp.get(url)
    data = json.loads(resp.body)

    expected = {'error': deps.MISSING_PARAM_ERROR}

    self.assertEqual(resp.status, 400)
    self.assertEqual(data, expected)

    # Missing git_hash
    url = '/api/deps?repository_url=foo'
    resp = self.testapp.get(url)
    data = json.loads(resp.body)

    self.assertEqual(resp.status, 400)
    self.assertEqual(data, expected)

  def testGet_NoDeps(self):
    # Missing, invalid, unparsable DEPS returns an empty frozendict(),
    self.file_contents.return_value = frozenset()

    url = '/api/deps?repository_url=' + test.CHROMIUM_URL + '&git_hash=bar'
    resp = self.testapp.get(url)
    data = json.loads(resp.body)

    expected = []

    self.assertEqual(resp.status, 200)
    self.assertEqual(data, expected)

  def testGet_MalformedDeps(self):
    self.file_contents.return_value = """
vars = {
  'chromium_git': 'https://chromium.googlesource.com',
}
deps = {
  'src/v8': Var('chromium_git') + '/v8/v8.git' + '@' + 'c092edb' + '@' + 'foo',
}
    """

    url = '/api/deps?repository_url=' + test.CHROMIUM_URL + '&git_hash=bar'
    resp = self.testapp.get(url)
    data = json.loads(resp.body)

    expected = {'error': deps.DEPS_MALFORMATTED_ERROR}

    self.assertEqual(resp.status, 400)
    self.assertEqual(data, expected)
