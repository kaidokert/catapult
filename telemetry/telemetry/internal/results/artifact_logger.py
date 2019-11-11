# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from telemetry.internal.results import artifact_compat_wrapper


artifact_impl = artifact_compat_wrapper.ArtifactCompatWrapperFactory(None)


def RegisterArtifactImplementation(artifact_implementation):
  """Register the artifact implementation used to log future artifacts.

  Args:
    artifact_implementation: The artifact implementation to use for future
        artifact creations. Must be supported in
        artifact_compat_wrapper.ArtifactCompatWrapperFactory.
  """
  global artifact_impl  # pylint: disable=global-statement
  artifact_impl = artifact_compat_wrapper.ArtifactCompatWrapperFactory(
      artifact_implementation)


def CreateArtifact(name, data):
  """Create an artifact with the given data.

    Args:
      name: The name of the artifact, can include '/' to specify subdirectories
          to be saved in.
      data: The data to write to the artifact.
    """
  artifact_impl.CreateArtifact(name, data)
