# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from dashboard.pinpoint.models.change import repository
from dashboard.pinpoint import test


class RepositoryTest(test.TestCase):

  def testRepositoryUrl(self):
    self.assertEqual(repository.RepositoryUrl('chromium'), test.CHROMIUM_URL)

  def testRepositoryUrlRaisesWithUnknownName(self):
    with self.assertRaises(KeyError):
      repository.RepositoryUrl('not chromium')

  def testRepository(self):
    name = repository.Repository(test.CHROMIUM_URL + '.git')
    self.assertEqual(name, 'chromium')

  def testRepositoryRaisesWithUnknownUrl(self):
    with self.assertRaises(KeyError):
      repository.Repository('https://googlesource.com/nonexistent/repo')

  def testAddRepository(self):
    name = repository.Repository('https://example/repo',
                                 add_if_missing=True)
    self.assertEqual(name, 'repo')

    self.assertEqual(repository.RepositoryUrl('repo'), 'https://example/repo')
    self.assertEqual(repository.Repository('https://example/repo'), 'repo')

  def testAddRepositoryRaisesWithDuplicateName(self):
    with self.assertRaises(AssertionError):
      repository.Repository('https://example/chromium', add_if_missing=True)
