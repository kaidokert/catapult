# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os

from pyfakefs import fake_filesystem_unittest

import dependency_manager

def _CreateFile(path, content):
  """Create file at specific |path|, with specific |content|."""
  parent_dir = os.path.dirname(path)
  if not os.path.exists(parent_dir):
    os.mkdir(parent_dir)
  with open(path, 'wb') as f:
    f.write(content)


def _ChangeFileTime(path, time0, days):
  new_time = time0 + (days * 24 * 60 * 60)
  os.utime(path, (new_time, new_time))

class LocalPathInfoTest(fake_filesystem_unittest.TestCase):

  def setUp(self):
    self.setUpPyfakefs()

  def tearDown(self):
    self.tearDownPyfakefs()

  def testEmptyInstance(self):
    path_info = dependency_manager.LocalPathInfo(None)
    self.assertIsNone(path_info.GetLocalPath())
    self.assertFalse(path_info.IsPathInLocalPaths('/test/file.txt'))

  def testSimpleGroupWithOnePath(self):
    path_info = dependency_manager.LocalPathInfo(['/test/file.txt'])
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file.txt'))
    self.assertFalse(path_info.IsPathInLocalPaths('/test/other.txt'))

    # GetLocalPath returns None if the file doesn't exist.
    # Otherwise it will return the file path.
    self.assertIsNone(path_info.GetLocalPath())
    _CreateFile('/test/file.txt', 'Hello\n')
    self.assertEqual('/test/file.txt', path_info.GetLocalPath())

  def testSimpleGroupsWithMultiplePaths(self):
    path_info = dependency_manager.LocalPathInfo(
        [['/test/file1', '/test/file2', '/test/file3']])
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file1'))
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file2'))
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file3'))

    _CreateFile('/test/file1', 'Hello')
    _CreateFile('/test/file2', 'Bonjour')
    _CreateFile('/test/file3', 'Ola')
    s = os.stat('/test/file1')
    time0 = s.st_mtime

    _ChangeFileTime('/test/file1', time0, 4)
    _ChangeFileTime('/test/file2', time0, 2)
    _ChangeFileTime('/test/file3', time0, 0)
    self.assertEqual('/test/file1', path_info.GetLocalPath())

    _ChangeFileTime('/test/file1', time0, 0)
    _ChangeFileTime('/test/file2', time0, 4)
    _ChangeFileTime('/test/file3', time0, 2)
    self.assertEqual('/test/file2', path_info.GetLocalPath())

    _ChangeFileTime('/test/file1', time0, 2)
    _ChangeFileTime('/test/file2', time0, 0)
    _ChangeFileTime('/test/file3', time0, 4)
    self.assertEqual('/test/file3', path_info.GetLocalPath())

  def testMultipleGroupsWithSinglePaths(self):
    path_info = dependency_manager.LocalPathInfo(
        ['/test/file1', '/test/file2', '/test/file3'])
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file1'))
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file2'))
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file3'))

    self.assertIsNone(path_info.GetLocalPath())
    _CreateFile('/test/file3', 'Hello')
    self.assertEqual('/test/file3', path_info.GetLocalPath())
    _CreateFile('/test/file2', 'World')
    self.assertEqual('/test/file2', path_info.GetLocalPath())
    _CreateFile('/test/file1', 'Bonjour')
    self.assertEqual('/test/file1', path_info.GetLocalPath())

  def testMultipleGroupsWithMultiplePaths(self):
    path_info = dependency_manager.LocalPathInfo([
        ['/test/file1', '/test/file2'],
        ['/test/file3', '/test/file4']])
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file1'))
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file2'))
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file3'))
    self.assertTrue(path_info.IsPathInLocalPaths('/test/file4'))

    _CreateFile('/test/file1', 'Hello')
    _CreateFile('/test/file3', 'Bonjour')
    s = os.stat('/test/file1')
    time0 = s.st_mtime

    # Check that file1 is always returned, even if it is not the most recent
    # file, because it is part of the first group and exists.
    _ChangeFileTime('/test/file1', time0, 2)
    _ChangeFileTime('/test/file3', time0, 0)
    self.assertEqual('/test/file1', path_info.GetLocalPath())

    _ChangeFileTime('/test/file1', time0, 0)
    _ChangeFileTime('/test/file3', time0, 2)
    self.assertEqual('/test/file1', path_info.GetLocalPath())

  def testUpdate(self):
    path_info1 = dependency_manager.LocalPathInfo(
        [['/test/file1', '/test/file2']])  # One group with two files.
    path_info2 = dependency_manager.LocalPathInfo(
        ['/test/file1', '/test/file2', '/test/file3'])  # Three groups
    self.assertTrue(path_info1.IsPathInLocalPaths('/test/file1'))
    self.assertTrue(path_info1.IsPathInLocalPaths('/test/file2'))
    self.assertFalse(path_info1.IsPathInLocalPaths('/test/file3'))

    _CreateFile('/test/file3', 'Hello')
    self.assertIsNone(path_info1.GetLocalPath())

    path_info1.Update(path_info2)
    self.assertTrue(path_info1.IsPathInLocalPaths('/test/file1'))
    self.assertTrue(path_info1.IsPathInLocalPaths('/test/file2'))
    self.assertTrue(path_info1.IsPathInLocalPaths('/test/file3'))
    self.assertEqual('/test/file3', path_info1.GetLocalPath())

    _CreateFile('/test/file1', 'Hello')
    time0 = os.stat('/test/file1').st_mtime
    _ChangeFileTime('/test/file3', time0, 2)  # Make file3 more recent.

    # Check that file3 is in a later group.
    self.assertEqual('/test/file1', path_info1.GetLocalPath())
