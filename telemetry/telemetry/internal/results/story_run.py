# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import datetime
import logging
import os
import random
import shutil
import time
import uuid

from py_utils import cloud_storage  # pylint: disable=import-error

from telemetry.internal.util import file_handle


PASS = 'PASS'
FAIL = 'FAIL'
SKIP = 'SKIP'


def _FormatTimeStamp(epoch):
  return datetime.datetime.utcfromtimestamp(epoch).isoformat() + 'Z'


def _FormatDuration(seconds):
  return '{:.2f}s'.format(seconds)


class Artifact(object):
  def __init__(self, local_path, content_type=None):
    self._local_path = local_path
    self._content_type = content_type
    self._url = None

  @property
  def local_path(self):
    return self._local_path

  @property
  def content_type(self):
    return self._content_type

  @property
  def url(self):
    return self._url

  def SetUrl(self, url):
    assert not self._url, 'Artifact URL has been already set'
    self._url = url


class StoryRun(object):
  def __init__(self, story, output_dir=None):
    self._story = story
    self._values = []
    self._tbm_metrics = []
    self._skip_reason = None
    self._skip_expected = False
    self._failed = False
    self._failure_str = None
    self._start_time = time.time()
    self._end_time = None
    self._artifacts = {}

    if output_dir is None:
      self._output_dir = None
      self._artifact_dir = None
    else:
      self._output_dir = os.path.realpath(output_dir)
      artifact_dir = 'artifacts_%s_%s_%s' % (
          self._story.name,
          _FormatTimeStamp(self._start_time),
          random.randint(1, 1e5),
      )
      self._artifact_dir = os.path.join(self._output_dir, artifact_dir)
      if not os.path.exists(self._artifact_dir):
        os.makedirs(self._artifact_dir)


  def AddValue(self, value):
    self._values.append(value)

  def SetTbmMetrics(self, metrics):
    assert not self._tbm_metrics, 'Metrics have already been set'
    assert len(metrics) > 0, 'Metrics should not be empty'
    self._tbm_metrics = metrics

  def SetFailed(self, failure_str):
    self._failed = True
    self._failure_str = failure_str

  def Skip(self, reason, is_expected=True):
    if not reason:
      raise ValueError('A skip reason must be given')
    # TODO(#4254): Turn this into a hard failure.
    if self.skipped:
      logging.warning(
          'Story was already skipped with reason: %s', self.skip_reason)
    self._skip_reason = reason
    self._skip_expected = is_expected

  def Finish(self):
    assert not self.finished, 'story run had already finished'
    self._end_time = time.time()

  def AsDict(self):
    """Encode as TestResultEntry dict in LUCI Test Results format.

    See: go/luci-test-results-design
    """
    assert self.finished, 'story must be finished first'
    return {
        'testResult': {
            'testName': self.test_name,
            'status': self.status,
            'isExpected': self.is_expected,
            'startTime': _FormatTimeStamp(self._start_time),
            'runDuration': _FormatDuration(self.duration)
        }
    }

  @property
  def story(self):
    return self._story

  @property
  def output_dir(self):
    return self._output_dir

  @property
  def test_name(self):
    # TODO(crbug.com/966835): This should be prefixed with the benchmark name.
    return self.story.name

  @property
  def values(self):
    """The values that correspond to this story run."""
    return self._values

  @property
  def tbm_metrics(self):
    """The TBMv2 metrics that will computed on this story run."""
    return self._tbm_metrics

  @property
  def status(self):
    if self.failed:
      return FAIL
    elif self.skipped:
      return SKIP
    else:
      return PASS

  @property
  def ok(self):
    return not self.skipped and not self.failed

  @property
  def skipped(self):
    """Whether the current run is being skipped."""
    return self._skip_reason is not None

  @property
  def skip_reason(self):
    return self._skip_reason

  @property
  def is_expected(self):
    """Whether the test status is expected."""
    return self._skip_expected or self.ok

  # TODO(#4254): Make skipped and failed mutually exclusive and simplify these.
  @property
  def failed(self):
    return not self.skipped and self._failed

  @property
  def failure_str(self):
    return self._failure_str

  @property
  def start_datetime(self):
    return datetime.datetime.utcfromtimestamp(self._start_time)

  @property
  def duration(self):
    return self._end_time - self._start_time

  @property
  def finished(self):
    return self._end_time is not None

  def _PrepareLocalPath(self, name):
    """ Ensure that the artifact with the given name can be created.

    Returns: absolute path to the artifact (file may not exist yet).
    """
    local_path = os.path.join(self._artifact_dir, *name.split('/'))
    if not os.path.exists(os.path.dirname(local_path)):
      os.makedirs(os.path.dirname(local_path))
    return local_path

  @contextlib.contextmanager
  def CreateArtifact(self, name):
    """Create an artifact.

    Args:
      * name: File path that this artifact will have inside the artifacts dir.
          The name can contain sub-directories with '/' as a separator.
    Returns:
      A generator yielding a file object.
    """
    if self._output_dir is None:  # for tests
      yield open(os.devnull, 'w')
      return

    assert name not in self._artifacts, (
        'Story already has an artifact: %s' % name)

    local_path = self._PrepareLocalPath(name)

    with open(local_path, 'w+b') as file_obj:
      self.AddArtifact(name, local_path)
      yield file_obj

  @contextlib.contextmanager
  def CaptureArtifact(self, name):
    """Generate an absolute file path for an artifact, but do not
    create a file. File creation is a responsibility of the caller of this
    method. It is assumed that the file exists at the exit of the context.

    Args:
      * name: File path that this artifact will have inside the artifacts dir.
          The name can contain sub-directories with '/' as a separator.
    Returns:
      A generator yielding a file name.
    """
    assert name not in self._artifacts, (
        'Story already has an artifact: %s' % name)

    local_path = self._PrepareLocalPath(name)
    yield local_path
    assert os.path.isfile(local_path), (
        'Failed to capture an artifact: %s' % local_path)
    self.AddArtifact(name, local_path)

  def AddArtifact(self, name, artifact_path):
    """Add an artifact.

    Args:
      * name: File path that this artifact will have inside the artifacts dir.
          The name can contain sub-directories with '/' as a separator.
      * artifact_path: The path to the artifact on disk. It will be moved
        to the artifact dir and renamed according to `name`.
    """
    if self._output_dir is None:  # for tests
      return

    assert name not in self._artifacts, (
        'Story already has an artifact: %s' % name)

    if isinstance(artifact_path, file_handle.FileHandle):
      artifact_path = artifact_path.GetAbsPath()
    artifact_path = os.path.realpath(artifact_path)

    local_path = self._PrepareLocalPath(name)

    if local_path != artifact_path:
      logging.warning('Renaming artifact file %r to %r' % (
          artifact_path, local_path))
      shutil.move(artifact_path, local_path)

    self._artifacts[name] = Artifact(local_path)

  def IterArtifacts(self, subdir=None):
    """Iterate over all artifacts in a given sub-directory.

    Returns an iterator over (name, artifact) tuples.
    """
    for name, artifact in self._artifacts.iteritems():
      if subdir is None or name.split('/', 1)[0] == subdir:
        yield name, artifact

  def GetArtifact(self, name):
    """Get artifact by name.

    Returns an Artifact object or None, if there's no artifact with this name.
    """
    return self._artifacts.get(name)

  def UploadArtifactsToCloud(self, bucket):
    """Upload all artifacts of the test to cloud storage.

    Sets 'url' attribute of each artifact to its cloud URL.
    """
    for name, artifact in self.IterArtifacts():
      artifact.SetUrl(cloud_storage.Insert(
          bucket, str(uuid.uuid1()), artifact.local_path))
      logging.warning('Uploading %s of page %s to %s\n' % (
          name, self._story.name, artifact.url))
