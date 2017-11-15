# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections
import tempfile

class ArtifactResults(object):
  def __init__(self):
    # Maps artifact name to location of data on disk
    self._story_artifacts = collections.defaultdict(dict)

  @property
  def results(self):
    return dict(self._story_artifacts)

  def AddArtifact(self, story, name, artifact_path=None, data=None):
    """Adds an artifact.

    Args:
      * story: The story being currently executed
      * name: The name of the artifact.
      * artifact_path: If present, the path to the artifact on disk.
      * data: If present, the data for the artifact. Will be written out to
              disk.
    """
    assert artifact_path or data, "One of artifact_path or data must be set"

    if data:
      _, tempfile_path = tempfile.mkstemp()
      with open(tempfile_path, 'w') as f:
        f.write(data)

      artifact_path = tempfile_path

    # Handle FileHandle objects
    if hasattr(artifact_path, 'GetAbsPath'):
      artifact_path = artifact_path.GetAbsPath()

    self._story_artifacts[story.name][name] = artifact_path
