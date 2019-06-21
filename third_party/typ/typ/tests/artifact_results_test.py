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
  def _VerifyPathAndContents(self, dirname, test_name, iteration, artifact_type,
      artifact_name, contents):
    path = os.path.join(
        dirname, test_name, iteration, artifact_type, artifact_name)
    self.assertTrue(os.path.exists(path))
    with open(path, 'r') as f:
      self.assertEqual(f.read(), contents)

  def test_create_artifact_writes_to_disk(self):
    """Tests CreateArtifact will write to disk at the correct location."""
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir, 'test_name', 0)
      with ar.CreateArtifact(
          'artifact_type', 'mime_type', 'artifact_name') as f:
        f.write('contents')

      self._VerifyPathAndContents(tempdir, 'test_name', '0', 'artifact_type',
          'artifact_name', 'contents')
    finally:
      shutil.rmtree(tempdir)

  def test_create_artifact_duplicate_matching_type(self):
    """Tests that creating artifacts with the same artifact type works."""
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir, 'test_name', 0)
      with ar.CreateArtifact(
          'artifact_type', 'mime_type', 'artifact_name') as f:
        f.write('contents')
      with ar.CreateArtifact(
          'artifact_type', 'mime_type', 'artifact_name2') as f:
        f.write('other contents')

      self._VerifyPathAndContents(tempdir, 'test_name', '0', 'artifact_type',
          'artifact_name', 'contents')
      self._VerifyPathAndContents(tempdir, 'test_name', '0', 'artifact_type',
          'artifact_name2', 'other contents')
    finally:
      shutil.rmtree(tempdir)

  def test_create_artifact_duplicate_mismatched_type(self):
    """Tests that CreateArtifact with mismatched artifact/mime types fails."""
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir, 'test_name', 0)
      with ar.CreateArtifact(
          'artifact_type', 'mime_type', 'artifact_name') as f:
        f.write('contents')
      with self.assertRaises(artifact_results.ArtifactTypeConflictError):
        with ar.CreateArtifact(
            'artifact_type', 'mime_type2', 'artifact_name2') as f:
          pass
    finally:
      shutil.rmtree(tempdir)

  def test_create_artifact_duplicate_name(self):
    """Tests that CreateArtifact with duplicate artifact name/type fails."""
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir, 'test_name', 0)
      with ar.CreateArtifact(
          'artifact_type', 'mime_type', 'artifact_name') as f:
        f.write('contents')
      with self.assertRaises(artifact_results.DuplicateArtifactError):
        with ar.CreateArtifact(
            'artifact_type', 'mime_type', 'artifact_name') as f:
          pass
    finally:
      shutil.rmtree(tempdir)

  def test_create_artifact_duplicate_name_different_type(self):
    """Tests that CreateArtifact with a duplicate name/different type works."""
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir, 'test_name', 0)
      with ar.CreateArtifact(
          'artifact_type', 'mime_type', 'artifact_name') as f:
        f.write('contents')
      with ar.CreateArtifact(
          'artifact_type2', 'mime_type', 'artifact_name') as f:
        f.write('other contents')

      self._VerifyPathAndContents(tempdir, 'test_name', '0', 'artifact_type',
          'artifact_name', 'contents')
      self._VerifyPathAndContents(tempdir, 'test_name', '0', 'artifact_type2',
          'artifact_name', 'other contents')
    finally:
      shutil.rmtree(tempdir)

  def test_duplicates_allowed_across_iterations(self):
    """Tests that using ArtifactResults with different iterations works."""
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir, 'test_name', 0)
      with ar.CreateArtifact(
          'artifact_type', 'mime_type', 'artifact_name') as f:
        f.write('contents')

      another_ar = artifact_results.ArtifactResults(tempdir, 'test_name', 1)
      with another_ar.CreateArtifact(
          'artifact_type', 'mime_type', 'artifact_name') as f:
        f.write('other contents')

      self._VerifyPathAndContents(tempdir, 'test_name', '0', 'artifact_type',
          'artifact_name', 'contents')
      self._VerifyPathAndContents(tempdir, 'test_name', '1', 'artifact_type',
          'artifact_name', 'other contents')
    finally:
      shutil.rmtree(tempdir)


class ArtifactResultsDataRetrievalTests(unittest.TestCase):
  def test_get_artifacts(self):
    """Tests that GetArtifacts returns the expected data."""
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir, 'test_name', 0)
      with ar.CreateArtifact(
          'artifact_type', 'mime_type', 'artifact_name') as f:
        pass

      self.assertEqual(ar.GetArtifacts(), {'artifact_type': [
          os.path.join('test_name', '0', 'artifact_type', 'artifact_name')]})
    finally:
      shutil.rmtree(tempdir)

  def test_get_artifact_types(self):
    """Tests that GetArtifactTypes returns the expected data."""
    tempdir = tempfile.mkdtemp()
    try:
      ar = artifact_results.ArtifactResults(tempdir, 'test_name', 0)
      with ar.CreateArtifact(
          'artifact_type', 'mime_type', 'artifact_name') as f:
        pass

      self.assertEqual(ar.GetArtifactTypes(), {'artifact_type': 'mime_type'})
    finally:
      shutil.rmtree(tempdir)
