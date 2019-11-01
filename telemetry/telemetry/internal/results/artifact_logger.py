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


def CreateArtifact(artifact_type, path, data):
  """Create an artifact with the given data.

    Args:
      artifact_type: The type of artifact, e.g. 'screenshot'.
      path: The path where the artifact will be saved relative to the artifact
          directory.
      data: The data to write to the artifact.
    """
  artifact_impl.CreateArtifact(artifact_type, path, data)


def WillLogArtifacts():
  """Returns whether the wrapper will log instead of creating an artifact.

    Returns:
      True iff the wrapper will log the given data instead of creating an
      artifact. Otherwise, False.
    """
  return artifact_impl.WillLogArtifacts()
