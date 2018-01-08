# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import collections
import logging
import os
import shutil
import tempfile

from telemetry.internal.util import file_handle


_ARTIFACT_DIRNAME = 'artifacts'


class NoopArtifactResults(object):
  """A no-op artifact results object."""
  def __init__(self, output_dir):
    self._artifact_dir = os.path.abspath(
        os.path.join(os.path.realpath(output_dir), _ARTIFACT_DIRNAME))

  @property
  def artifact_dir(self):
    return self._artifact_dir

  def IterTestAndArtifacts(self):
    return
    yield  # pylint: disable=unreachable

  def GetTestArtifacts(self, test_name):
    del test_name
    return {}

  def CreateArtifact(self, story, name, run_number=None):
    del story, name, run_number
    return open(os.devnull, 'w')

  def AddArtifact(self, test_name, name, artifact_path, run_number=None):
    del run_number
    if isinstance(artifact_path, file_handle.FileHandle):
      artifact_path = artifact_path.GetAbsPath()
    if os.path.exists(artifact_path):
      logging.info("Deleting unused artifact %r of %r" % (name, test_name))
      os.unlink(artifact_path)


class ArtifactResults(object):
  """Stores artifacts from test runs."""
  def __init__(self, output_dir):
    """Creates an artifact results object.

    Args:
      output_dir: The output directory where artifacts should be dumped.
    """
    # Maps test name -> mapping of artifact name to list of artifacts
    self._test_artifacts = collections.defaultdict(
        lambda: collections.defaultdict(list))
    self._artifact_dir = os.path.abspath(os.path.join(
        os.path.realpath(output_dir), _ARTIFACT_DIRNAME))

    if not os.path.exists(self.artifact_dir):
      os.makedirs(self.artifact_dir)

  def IterTestAndArtifacts(self):
    """ Iter all artifacts by |test_name| and corresponding |artifacts|.

      test_name: the name of test in string
      artifacts: a dictionary whose keys are the name of artifact type
        (e.g: 'screenshot', 'log'..) and values are the list of file paths of
        those artifacts.
    """
    for test_name, artifacts in self._test_artifacts.iteritems():
      yield test_name, artifacts

  def GetTestArtifacts(self, test_name):
    """Gets all artifacts for a test.

    Returns a dict mapping artifact name to a list of relative filepaths.
    """
    return self._test_artifacts[test_name]

  @property
  def artifact_dir(self):
    return self._artifact_dir

  def GetAbsPath(self, artifact_path):
    """ Returns absolute path to artifact_path stored in |artifact_dir|.

    Note: this does not check whether |artifact_path| actually exists.
    """
    if artifact_path.startswith(self._artifact_dir):
      return artifact_path
    assert artifact_path.startswith(_ARTIFACT_DIRNAME), (
        'artifact_path must either be absolute path or relative to '
        'output directory. Unrecognized path: %s' % artifact_path)
    output_dir = os.path.join(self._artifact_dir, '..')
    return os.path.join(output_dir, artifact_path)


  @contextlib.contextmanager
  def CreateArtifact(self, story, name, run_number=None):
    """Create an artifact.

    Args:
      * story: The name of the story this artifact belongs to.
      * name: The name of this artifact; 'logs', 'screenshot'.
      * run_number: Which run of a test this is. If the current number of
          artifacts for the (test_name, name) key is less than this number,
          new `None` artifacts will be inserted, with the assumption that
          other runs of this test did not produce the same set of artifacts.
          NOT CURRENTLY IMPLEMENTED.
    Returns:
      A generator yielding a file object.
    """
    del run_number
    with tempfile.NamedTemporaryFile(
        prefix='telemetry_test', dir=self._artifact_dir,
        delete=False) as file_obj:
      self.AddArtifact(story, name, file_obj.name)
      yield file_obj

  def AddArtifact(self, test_name, name, artifact_path, run_number=None):
    """Adds an artifact.

    Args:
      * test_name: The test which produced the artifact.
      * name: The name of the artifact.
      * artifact_path: The path to the artifact on disk. If it is not in the
          proper artifact directory, it will be moved there.
      * run_number: Which run of a test this is. If the current number of
          artifacts for the (test_name, name) key is less than this number,
          new `None` artifacts will be inserted, with the assumption that
          other runs of this test did not produce the same set of artifacts.
          NOT CURRENTLY IMPLEMENTED.
    """
    del run_number
    if isinstance(artifact_path, file_handle.FileHandle):
      artifact_path = artifact_path.GetAbsPath()

    artifact_path = os.path.realpath(artifact_path)

    # If the artifact isn't in the artifact directory, move it.
    if not artifact_path.startswith(self.artifact_dir + os.sep):
      logging.warning("Moving artifact file %r to %r" % (
          artifact_path, self.artifact_dir))
      shutil.move(artifact_path, self.artifact_dir)
      artifact_path = os.path.basename(artifact_path)
    else:
      # Make path relative to artifact directory.
      artifact_path = artifact_path[len(self.artifact_dir + os.sep):]

    # '/' is interpreted as a generic path separator. We want these paths to be
    # relative to the output directory. The filter is there because
    # os.path.split returns an empty string when run on a filename;
    # os.path.split('bar') -> ('', 'bar').
    artifact_path = '/'.join([_ARTIFACT_DIRNAME] + list(
        path for path in os.path.split(artifact_path) if path))

    self._test_artifacts[test_name][name].append(artifact_path)
