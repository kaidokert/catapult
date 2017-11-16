# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections
import os
import shutil

from telemetry.internal.util import file_handle


class ArtifactResults(object):
  """Stores artifacts from test runs."""
  def __init__(self, output_dir):
    # Maps test name -> mapping of artifact name to list of artifacts
    self._test_artifacts = collections.defaultdict(
        lambda: collections.defaultdict(list))
    self._output_dir = output_dir

    if not os.path.exists(self.artifact_dir):
      os.makedirs(self.artifact_dir)

  def GetArtifact(self, test_name):
    return self._test_artifacts[test_name]

  @property
  def artifact_dir(self):
    return os.path.join(self._output_dir, 'artifacts')

  def AddArtifact(self, test_name, name, artifact_path):
    """Adds an artifact.

    Args:
      * test_name: The test which produced the artifact.
      * name: The name of the artifact.
      * artifact_path: The path to the artifact on disk. If it is not in the
          proper artifact directory, it will be moved there.
    """
    if isinstance(artifact_path, file_handle.FileHandle):
      artifact_path = artifact_path.GetAbsPath()

    # If the artifact isn't in the artifact directory, move it.
    if not artifact_path.startswith(self.artifact_dir):
      shutil.move(artifact_path, self.artifact_dir)

    # Make path relative to artifact directory.
    artifact_path = artifact_path[len(self.artifact_dir + '/'):]

    self._test_artifacts[test_name][name].append(artifact_path)
