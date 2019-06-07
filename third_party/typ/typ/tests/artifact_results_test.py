# Copyright 2019 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import tempfile
import unittest

from typ import artifact_results

class ArtifactResultsArtifactCreationTests(unittest.TestCase):
  def test_create_artifact_writes_to_disk(self):
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir)
      ar.EnsureArtifactTypeDefined('artifact_type', 'mime_type')
      with ar.CreateArtifact(
          'test_name', 'artifact_type', 'artifact_name') as f:
        f.write('contents')

      path = os.path.join(tempdir, ar.ARTIFACT_DIRNAME, 'test_name',
                          'artifact_type', 'artifact_name')
      self.assertTrue(os.path.exists(path))
      with open(path, 'r') as f:
        self.assertEqual(f.read(), 'contents')
    finally:
      shutil.rmtree(tempdir)

  def test_create_artifact_duplicates_allowed(self):
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir)
      ar.EnsureArtifactTypeDefined('artifact_type', 'mime_type')
      with ar.CreateArtifact(
          'test_name', 'artifact_type', 'artifact_name.ext') as f:
        f.write('contents1')
      with ar.CreateArtifact(
          'test_name', 'artifact_type', 'artifact_name.ext') as f:
        f.write('contents2')

      path1 = os.path.join(tempdir, ar.ARTIFACT_DIRNAME, 'test_name',
                          'artifact_type', 'artifact_name.ext')
      path2 = os.path.join(tempdir, ar.ARTIFACT_DIRNAME, 'test_name',
                          'artifact_type', 'artifact_name_.ext')
      self.assertTrue(os.path.exists(path1))
      self.assertTrue(os.path.exists(path2))
      with open(path1, 'r') as f:
        self.assertEqual(f.read(), 'contents1')
      with open(path2, 'r') as f:
        self.assertEqual(f.read(), 'contents2')
    finally:
      shutil.rmtree(tempdir)

  def test_create_artifact_duplicates_not_allowed(self):
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir)
      ar.EnsureArtifactTypeDefined('artifact_type', 'mime_type')
      with ar.CreateArtifact(
          'test_name', 'artifact_type', 'artifact_name.ext') as f:
        f.write('contents1')
      with self.assertRaises(RuntimeError):
        with ar.CreateArtifact('test_name', 'artifact_type',
                               'artifact_name.ext',
                               allow_duplicates=False) as f:
          pass
    finally:
      shutil.rmtree(tempdir)

  def test_invalid_artifact_type(self):
    ar = artifact_results.ArtifactResults('testdir')
    with self.assertRaises(ValueError):
      with ar.CreateArtifact('test_name', 'artifact_type', 'artifact_name'):
        pass

  def test_artifact_paths_are_relative(self):
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir)
      ar.EnsureArtifactTypeDefined('artifact_type', 'mime_type')
      with ar.CreateArtifact(
          'test_name', 'artifact_type', 'artifact_name') as f:
        f.write('contents')
      artifacts = ar.GetArtifactsForTest('test_name')
      self.assertIn('artifact_type', artifacts)
      self.assertEqual(len(artifacts['artifact_type']), 1)
      relpath = os.path.join(
          ar.ARTIFACT_DIRNAME, 'test_name', 'artifact_type', 'artifact_name')
      self.assertEqual(artifacts['artifact_type'][0], relpath)
    finally:
      shutil.rmtree(tempdir)


class ArtifactResultsArtifactTypeTests(unittest.TestCase):
  def test_add_artifact_type(self):
    ar = artifact_results.ArtifactResults('testdir')
    ar.EnsureArtifactTypeDefined('artifact_type', 'mime_type')
    types = ar.GetArtifactTypes()
    self.assertIn('artifact_type', types)
    self.assertEqual('mime_type', types['artifact_type'])

  def test_readd_matching_mime_type(self):
    ar = artifact_results.ArtifactResults('testdir')
    ar.EnsureArtifactTypeDefined('artifact_type', 'mime_type')
    ar.EnsureArtifactTypeDefined('artifact_type', 'mime_type')
    types = ar.GetArtifactTypes()
    self.assertIn('artifact_type', types)
    self.assertEqual('mime_type', types['artifact_type'])

  def test_readd_mismatched_mime_type(self):
    ar = artifact_results.ArtifactResults('testdir')
    ar.EnsureArtifactTypeDefined('artifact_type', 'mime_type')
    with self.assertRaises(ValueError):
      ar.EnsureArtifactTypeDefined('artifact_type', 'another_mime_type')
