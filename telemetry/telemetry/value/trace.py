# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import shutil
import sys
import tempfile

from py_utils import cloud_storage  # pylint: disable=import-error

from telemetry.internal.util import file_handle
from telemetry import value as value_module


_CLOUD_URL = (
    'https://console.developers.google.com/m/cloudstorage/b/{bucket}/o/{path}')


class TraceValue(value_module.Value):
  def __init__(self, page, trace_data, filename=None, local_dir=None,
               upload_bucket=None,
               # TODO(crbug.com/928278): Remove these deprecated args.
               file_path=None, remote_path=None,
               cloud_url=None, trace_url=None):
    """A value that contains trace data and knows how to serialize it.

    Args:
      page: A Page object for which the trace was recorded.
      trace_data: A trace data object where tracing data has been written to.
      filename: A file name to use when serializing the trace as HTML.
      local_dir: An optional path on the host where to place a serialized copy
        of the trace.
      upload_bucket: An optional string with the name of a cloud storage bucket
        where to upload the serialized trace data.
    """
    super(TraceValue, self).__init__(
        page, name='trace', units='', important=False, description=None,
        tir_label=None, grouping_keys=None)
    self._trace_data = trace_data
    self._filename = filename
    self._local_dir = local_dir
    self._upload_bucket = upload_bucket
    self._temp_file = None
    self._serialized_file_handle = None
    self._timeline_based_metrics = None

    # TODO(crbug.com/928278): Remove this validation code when the deprecated
    # args are no longer used.
    if file_path is not None:
      assert self._filename is None
      self._local_dir, self._filename = os.path.split(file_path)
    if remote_path is not None:
      if self._filename is None:
        self._filename = remote_path
      else:
        assert self._filename == remote_path
    if cloud_url is not None:
      assert self.cloud_url == cloud_url
    if trace_url is not None:
      assert self.trace_url == trace_url

  @property
  def serialized_file(self):
    assert self._temp_file is not None, 'Trace has not been serialized'
    return self._temp_file.GetAbsPath()

  @property
  def local_file(self):
    if self._filename is not None and self._local_dir is not None:
      return os.path.abspath(os.path.join(self._local_dir, self._filename))
    else:
      return None

  @property
  def cloud_url(self):
    if self._filename is not None and self._upload_bucket is not None:
      return _CLOUD_URL.format(bucket=self._upload_bucket, path=self._filename)
    else:
      return None

  @property
  def trace_url(self):
    if self.cloud_url is not None:
      return self.cloud_url
    elif self.local_file is not None:
      return 'file://' + self.local_file
    else:
      return None

  @property
  def value(self):
    if self.cloud_url:
      return self.cloud_url
    elif self._serialized_file_handle:
      return self._serialized_file_handle.GetAbsPath()

  def SerializeTraceData(self):
    if not self._temp_file:
      self._temp_file = self._GetTempFileHandle(self._trace_data)

  def _GetTempFileHandle(self, trace_data):
    tf = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
    tf.close()
    title = ''
    if self.page:
      title = self.page.name
    trace_data.Serialize(tf.name, trace_title=title)
    return file_handle.FromFilePath(tf.name)

  def __repr__(self):
    if self.page:
      page_name = self.page.name
    else:
      page_name = 'None'
    return 'TraceValue(%s, %s)' % (page_name, self.name)

  def SetTimelineBasedMetrics(self, metrics):
    assert not self._temp_file, 'Trace data should not already be serialized.'
    self._timeline_based_metrics = metrics

  def CleanUp(self):
    """Cleans up tempfile after it is no longer needed.

    A cleaned up TraceValue cannot be used for further operations. CleanUp()
    may be called more than once without error.
    """
    if self._trace_data:
      self._trace_data.CleanUpAllTraces()
      self._trace_data = None

    if self._temp_file is None:
      return
    os.remove(self._temp_file.GetAbsPath())
    self._temp_file = None

  def __enter__(self):
    return self

  def __exit__(self, _, __, ___):
    self.CleanUp()

  @property
  def cleaned_up(self):
    return self._temp_file is None and self._trace_data is None

  @property
  def is_serialized(self):
    return self._temp_file is not None

  @property
  def timeline_based_metric(self):
    return self._timeline_based_metrics

  @staticmethod
  def GetJSONTypeName():
    return 'trace'

  @classmethod
  def MergeLikeValuesFromSamePage(cls, values):
    assert len(values) > 0
    return values[0]

  @classmethod
  def MergeLikeValuesFromDifferentPages(cls, values):
    return None

  def AsDict(self):
    if self._temp_file is None:
      raise ValueError('Tried to serialize TraceValue without tempfile.')
    d = super(TraceValue, self).AsDict()
    if self._serialized_file_handle:
      d['file_id'] = self._serialized_file_handle.id
    if self.local_file is not None:
      d['file_path'] = self.local_file
    if self.cloud_url:
      d['cloud_url'] = self.cloud_url
    return d

  def Serialize(self):
    """Serialize the trace data to a local output directory."""
    if self._temp_file is None:
      raise ValueError('Tried to serialize nonexistent trace.')
    if self.local_file is None:
      raise ValueError('Tried to serialize trace with no local_file set.')
    shutil.copy(self._temp_file.GetAbsPath(), self.local_file)
    self._serialized_file_handle = file_handle.FromFilePath(self.local_file)
    return self._serialized_file_handle

  def UploadToCloud(self):
    if self._temp_file is None:
      raise ValueError('Tried to upload nonexistent trace to Cloud Storage.')
    if self.cloud_url is None:
      raise ValueError('Tried to upload trace with no cloud_url set.')
    try:
      if self._serialized_file_handle:
        fh = self._serialized_file_handle
      else:
        fh = self._temp_file
      cloud_storage.Insert(
          self._upload_bucket, self._filename, fh.GetAbsPath())
      sys.stderr.write(
          'View generated trace files online at %s for story %s\n' %
          (self.cloud_url, self.page.name if self.page else 'unknown'))
    except cloud_storage.PermissionError as e:
      logging.error('Cannot upload trace files to cloud storage due to '
                    ' permission error: %s' % e.message)
