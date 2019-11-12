# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Compatability layer for using different artifact implementations through a
# single API.
# TODO(https://crbug.com/1023458): Remove this once artifact implementations are
# unified.

import logging

from telemetry.internal.results import story_run

from typ import artifacts


def ArtifactCompatabilityWrapperFactory(artifact_impl):
  if isinstance(artifact_impl, story_run.StoryRun):
    return TelemetryArtifactCompatabilityWrapper(artifact_impl)
  elif isinstance(artifact_impl, artifacts.Artifacts):
    return TypArtifactCompatabilityWrapper(artifact_impl)
  elif artifact_impl is None:
    return LoggingArtifactCompatabilityWrapper()
  raise RuntimeError('Given unsupported artifact implementation %s' %
                     type(artifact_impl).__name__)


class ArtifactCompatabilityWrapper(object):
  def __init__(self, artifact_impl):
    self._artifact_impl = artifact_impl

  def CreateArtifact(self, name, data):
    """Create an artifact with the given data.

    Args:
      name: The name of the artifact, can include '/' to specify subdirectories
          to be saved in.
      data: The data to write to the artifact.
    """
    raise NotImplementedError()


class TelemetryArtifactCompatabilityWrapper(ArtifactCompatabilityWrapper):
  """Wrapper around Telemetry's story_run.StoryRun class."""
  def CreateArtifact(self, name, data):
    with self._artifact_impl.CreateArtifact(name) as f:
      f.write(data)


class TypArtifactCompatabilityWrapper(ArtifactCompatabilityWrapper):
  """Wrapper around typ's Artifacts class"""
  def CreateArtifact(self, name, data):
    # Approximate the artifact type using the full name. E.g.
    # "screenshots/failure_screenshot.png" will get the type "screenshots".
    artifact_type = name.split('/')[0].split('.')[0]
    self._artifact_impl.CreateArtifact(artifact_type, name, data)


class LoggingArtifactCompatabilityWrapper(ArtifactCompatabilityWrapper):
  """Wrapper that logs instead of actually creating artifacts.

  This is necessary because some tests, e.g. those that inherit from
  browser_test_case.BrowserTestCase, don't currently have a way of reporting
  artifacts. In those cases, we can fall back to logging to stdout so that
  information isn't lost. However, to prevent cluttering up stdout, we only log
  the first 100 characters.
  """
  def __init__(self):
    super(LoggingArtifactCompatabilityWrapper, self).__init__(None)

  def CreateArtifact(self, name, data):
    logging.warning(
        'Only logging the first 100 characters of the given artifact. To store '
        'the full artifact, run the test in either a Telemetry or typ context.')
    logging.info(
        'Artifact with name %s: %s', name, data[:min(100, len(data))])
