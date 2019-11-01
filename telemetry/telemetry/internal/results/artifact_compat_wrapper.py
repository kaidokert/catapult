# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Compatability layer for using different artifact implementations through a
# single API.
# TODO(file a bug): Remove this once artifact implementations are unified.

import logging

from telemetry.internal.results import story_run

from typ import artifacts

def ArtifactCompatWrapperFactory(artifact_impl):
  if isinstance(artifact_impl, story_run.StoryRun):
    return TelemetryArtifactCompatWrapper(artifact_impl)
  elif isinstance(artifact_impl, artifacts.Artifacts):
    return TypArtifactCompatWrapper(artifact_impl)
  elif artifact_impl is None:
    return LoggingArtifactCompatWrapper()
  raise RuntimeError('Given unsupported artifact implementation %s' %
                     type(artifact_impl).__name__)


class ArtifactCompatWrapper(object):
  def __init__(self, artifact_impl):
    self._artifact_impl = artifact_impl

  def CreateArtifact(self, artifact_type, path, data):
    """Create an artifact with the given data.

    Args:
      artifact_type: The type of artifact, e.g. 'screenshot'.
      path: The path where the artifact will be saved relative to the artifact
          directory.
      data: The data to write to the artifact.
    """
    raise NotImplementedError()

  def WillLogArtifacts(self):
    """Returns whether the wrapper will log instead of creating an artifact.

    Returns:
      True iff the wrapper will log the given data instead of creating an
      artifact. Otherwise, False.
    """
    return False


class TelemetryArtifactCompatWrapper(ArtifactCompatWrapper):
  """Wrapper around Telemetry's story_run.StoryRun class."""
  def CreateArtifact(self, artifact_type, path, data):
    del artifact_type  # unused.
    with self._artifact_impl.CreateArtifact(path) as f:
      f.write(data)


class TypArtifactCompatWrapper(ArtifactCompatWrapper):
  """Wrapper around typ's Artifacts class"""
  def CreateArtifact(self, artifact_type, path, data):
    self._artifact_impl.CreateArtifact(artifact_type, path, data)


class LoggingArtifactCompatWrapper(ArtifactCompatWrapper):
  """Wrapper that logs instead of actually creating artifacts.

  This is necessary because some tests, e.g. those that inherit from
  browser_test_case.BrowserTestCase, don't currently have a way of reporting
  artifacts. In those cases, we can fall back to logging to stdout so that
  information isn't lost.
  """
  def __init__(self):
    super(LoggingArtifactCompatWrapper, self).__init__(None)

  def CreateArtifact(self, artifact_type, path, data):
    logging.info(
        'Artifact with type %s and path %s: %s', artifact_type, path, data)

  def WillLogArtifacts(self):
    return True
