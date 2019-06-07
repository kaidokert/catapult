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

import contextlib
import logging
import os
import tempfile

class ArtifactResultsBase(object):
  def __init__(self):
    pass

  def EnsureArtifactTypeDefined(self, artifact_type, mime_type):
    raise NotImplementedError(
        'EnsureArtifactTypeDefined not implemented in subclass')

  def CreateArtifact(self, test_name, artifact_name, artifact_type,
                     allow_duplicates=True):
    raise NotImplementedError('CreateArtifact not implemented in subclass')

  def GetArtifactsForTest(self, test_name):
    raise NotImplementedError('GetArtifactsForTest not implemented in subclass')

  def GetArtifactTypes(self):
    raise NotImplementedError('GetArtifactTypes not implemented in subclass')


class ArtifactResults(ArtifactResultsBase):
  ARTIFACT_DIRNAME = 'artifacts'
  # Artifact types that have some sort of special processing logic in recipes,
  # and thus must not have test-configurable MIME types.
  RESERVED_ARTIFACT_TYPES = {
    'link': 'text/plain',
  }

  def __init__(self, output_dir):
    """Creates an artifact results object.

    This provides a way for tests to write arbitrary files to disk, either to
    be processed at a later point by a recipe or merge script, or simply as a
    way of saving additional data for users to later view.

    Artifacts are saved to disk in the following hierarchy in the output
    output directory:
      * 'artifacts'
      * test name
      * artifact type
      * artifact name

    See https://chromium.googlesource.com/chromium/src/+/master/docs/testing/json_test_results_format.md
    for documentation on the output format for artifacts.

    Args:
      output_dir: The output directory where artifacts will be saved to.
    """
    self._output_dir = output_dir
    self._artifact_dir = os.path.join(
        os.path.realpath(output_dir), ArtifactResults.ARTIFACT_DIRNAME)
    # A map of test names to dicts of artifact types to lists of filepaths. The
    # filepaths are relative to the output directory.
    self._artifact_map = {}
    self._artifact_type_map = ArtifactResults.RESERVED_ARTIFACT_TYPES.copy()

  def EnsureArtifactTypeDefined(self, artifact_type, mime_type):
    """Ensures that the given artifact to MIME type mapping is defined.

    If the mapping already exists and matches, this is a NOOP. If the mapping
    exists but does not match, an exception is raised. If the mapping does not
    exist, it is added.

    Args:
      artifact_type: A string specifying the artifact type to potentially add.
      mime_type: A string specifying the MIME type to correspond to the given
          |artifact_type|.

    Raises:
      ValueError if the given |artifact_type| is already defined, but its
          existing MIME type does not match |mime_type|."""
    if artifact_type in self._artifact_type_map:
      if self._artifact_type_map[artifact_type] == mime_type:
        return
      raise ValueError(
          'Given artifact type %s already defined with different MIME type. '
          'Given "%s", expected "%s".' % (
              artifact_type, mime_type, self._artifact_type_map[artifact_type]))
    self._artifact_type_map[artifact_type] = mime_type

  @contextlib.contextmanager
  def CreateArtifact(self, test_name, artifact_type, artifact_name,
                     allow_duplicates=True):
    """Creates an artifact and yields a handle to its File object.

    Args:
      test_name: A string specifying the test name for the artifact.
      artifact_type: A string specifying the artifact type for the artifact.
      artifact_name: A string specifying the name for the artifact.
      allow_duplicates: If true, duplicate artifacts will be resolved by
          appending underscores to the end of the filename. If false, duplicate
          artifacts will result in a RuntimeError being raised.

    Returns:
      A generator yielding a File object.

    Raises:
      RuntimeError if the given |artifact_name| already exists and
          |allow_duplicates| is false.
      ValueError if the given |artifact_type| is not defined.
    """
    if artifact_type not in self._artifact_type_map:
      raise ValueError(
          'Given artifact type %s is not defined. Call '
          'EnsureArtifactTypeDefined at least once beforehand to define it.' %
              artifact_type)

    if not allow_duplicates and self._DuplicateArtifactExists(
        test_name, artifact_type, artifact_name):
      raise RuntimeError(
          'Artifact named %s of type %s already exists for test %s.' % (
              artifact_name, artifact_type, test_name))

    while self._DuplicateArtifactExists(
        test_name, artifact_type, artifact_name):
      logging.warning(
          'Artifact %s of type %s already exists for test %s. Deduplicating.',
          artifact_name, artifact_type, test_name)
      filename, ext = os.path.splitext(artifact_name)
      artifact_name = filename + '_' + ext

    self._EnsureArtifactDir(test_name, artifact_type)

    if test_name not in self._artifact_map:
      self._artifact_map[test_name] = {}
    if artifact_type not in self._artifact_map[test_name]:
      self._artifact_map[test_name][artifact_type] = []
    self._artifact_map[test_name][artifact_type].append(
        self._GenerateRelativeArtifactPath(
            test_name, artifact_type, artifact_name))

    with open(self._GenerateFullArtifactPath(
        test_name, artifact_type, artifact_name), 'wb') as f:
      yield f

  def GetArtifactsForTest(self, test_name):
    return self._artifact_map.get(test_name, {})

  def GetArtifactTypes(self):
    return self._artifact_type_map

  def _EnsureArtifactDir(self, test_name, artifact_type):
    path = os.path.dirname(
        self._GenerateFullArtifactPath(test_name, artifact_type, 'a'))
    if not os.path.exists(path):
      os.makedirs(path)

  def _DuplicateArtifactExists(self, test_name, artifact_type, artifact_name):
    artifact_path = self._GenerateRelativeArtifactPath(
        test_name, artifact_type, artifact_name)
    artifacts = self._artifact_map.get(test_name, {}).get(artifact_type, [])
    return artifact_path in artifacts

  def _GenerateFullArtifactPath(self, test_name, artifact_type,
                                artifact_name):
    return os.path.join(
        self._artifact_dir, test_name, artifact_type, artifact_name)

  def _GenerateRelativeArtifactPath(self, test_name, artifact_type,
                                    artifact_name):
    path = self._GenerateFullArtifactPath(
        test_name, artifact_type, artifact_name)
    return os.path.relpath(path, self._output_dir)


class NoopArtifactResults(ArtifactResultsBase):
  def __init__(self):
    """An ArtifactResults object that doesn't really do anything.

    Meant to be used in the case that an output directory is not provided so
    that tests don't have to worry about that detail."""
    pass

  def EnsureArtifactTypeDefined(self, artifact_type, mime_type):
    del artifact_type, mime_type

  @contextlib.contextmanager
  def CreateArtifact(self, test_name, artifact_type, artifact_name,
                     allow_duplicates=True):
    del test_name, artifact_type, artifact_name, allow_duplicates
    yield tempfile.TemporaryFile()

  def GetArtifactsForTest(self, test_name):
    del test_name
    return {}

  def GetArtifactTypes(self):
    return {}
