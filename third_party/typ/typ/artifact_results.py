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
import os


class ArtifactTypeConflictError(RuntimeError):
  """Exception for re-registering an artifact with a conflicting MIME type."""
  pass


class DuplicateArtifactError(RuntimeError):
  """Exception for creating a duplicate artifact name/type combination."""
  pass


class ArtifactResults(object):
  def __init__(self, output_dir, test_name, iteration):
    """Creates an artifact results object.

    This provides a way for tests to write arbitrary files to disk, either to
    be processed at a later point by a recipe or merge script, or simply as a
    way of saving additional data for users to later view.

    Artifacts are saved to disk in the following hierarchy in the output
    directory:
      * test name
      * iteration
      * artifact type
      * artifact name

    See https://chromium.googlesource.com/chromium/src/+/master/docs/testing/json_test_results_format.md
    for documentation on the output format for artifacts.

    Args:
      output_dir: The directory that artifacts should be saved to on disk.
      test_name: The name of the test associated with this ArtifactResults
          instance.
      iteration: Which iteration of the test this is. Used to distinguish
          artifacts from different runs of the same test.
    """
    self._artifact_type_map = {}
    self._output_dir = output_dir
    self._test_name = test_name
    self._iteration = iteration
    # A map of artifact types to lists of filepaths of artifacts relative to the
    # output directory.
    self._artifact_map = {}

  @contextlib.contextmanager
  def CreateArtifact(self, artifact_type, mime_type, artifact_name):
    """Creates an artifact and yields a handle to its File object.

    Args:
      artifact_type: A string specifying the artifact type to add.
      mime_type: A string specifying the MIME type to correspond to the given
          |artifact_type|.
      artifact_name: A string specifying the name for the artifact.

    Raises:
      ArtifactTypeConflictError if the given |artifact_type| is already defined,
          but its existing MIME type does not match |mime_type|.
      DuplicateArtifactError if the given |artifact_type|/|artifact_name|
          combination was already created for this test run.
      OSError if the file can not be created for some reason.
    """
    self._EnsureArtifactTypeDefined(artifact_type, mime_type)
    existing_paths = self._artifact_map.get(artifact_type, [])
    artifact_path = self._GenerateRelativeArtifactPath(
        artifact_type, artifact_name)
    if artifact_path in existing_paths:
      raise DuplicateArtifactError(
          'Artifact %s with type %s already exists' % (
              artifact_name, artifact_type))

    full_artifact_path = os.path.join(self._output_dir, artifact_path)
    if not os.path.exists(os.path.dirname(full_artifact_path)):
      os.makedirs(os.path.dirname(full_artifact_path))

    if artifact_type not in self._artifact_map:
      self._artifact_map[artifact_type] = []
    self._artifact_map[artifact_type].append(artifact_path)
    with open(full_artifact_path, 'wb') as f:
      yield f

  def GetArtifacts(self):
    return self._artifact_map

  def GetArtifactTypes(self):
    return self._artifact_type_map

  def CreateScreenshot(self, artifact_name):
    return self.CreateArtifact('screenshot', 'image/png', artifact_name)

  def CreateLog(self, artifact_name):
    return self.CreateArtifact('log', 'text/plain', artifact_name)

  def CreateLink(self, artifact_name):
    return self.CreateArtifact('link', 'text/plain', artifact_name)

  def CreateTrace(self, artifact_name):
    return self.CreateArtifact('trace', 'application/json', artifact_name)

  def _GenerateRelativeArtifactPath(self, artifact_type, artifact_name):
    return os.path.join(self._test_name, str(self._iteration), artifact_type, artifact_name)

  def _EnsureArtifactTypeDefined(self, artifact_type, mime_type):
    if artifact_type in self._artifact_type_map:
      if self._artifact_type_map[artifact_type] == mime_type:
        return
      raise ArtifactTypeConflictError(
          'Given artifact type %s already defined with different MIME type. '
          'Given "%s", expected "%s".' % (
              artifact_type, mime_type, self._artifact_type_map[artifact_type]))
    self._artifact_type_map[artifact_type] = mime_type
