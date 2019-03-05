# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import shutil
import tempfile
import unittest

import mock

from telemetry import story
from telemetry import page as page_module
from telemetry.value import trace
from tracing.trace_data import trace_data


class ValueTest(unittest.TestCase):
  def testRepr(self):
    story_set = story.StorySet(base_dir=os.path.dirname(__file__))
    page = page_module.Page('http://www.bar.com/', story_set,
                            story_set.base_dir, name='http://www.bar.com/')
    v = trace.TraceValue(
        page, trace_data.CreateTraceDataFromRawData([{'test': 1}]))

    self.assertEquals('TraceValue(http://www.bar.com/, trace)', str(v))

  @mock.patch('telemetry.value.trace.cloud_storage.Insert')
  def testAsDictWhenTraceSerializedAndUploaded(self, insert_mock):
    tempdir = tempfile.mkdtemp()
    try:
      v = trace.TraceValue(
          None, trace_data.CreateTraceDataFromRawData([{'test': 1}]),
          filename='test.html',
          local_dir=tempdir,
          upload_bucket=trace.cloud_storage.PUBLIC_BUCKET)
      v.SerializeTraceData()
      fh = v.Serialize()
      v.UploadToCloud()
      d = v.AsDict()
      self.assertEqual(d['file_id'], fh.id)
      self.assertEqual(d['file_path'], v.local_file)
      self.assertEqual(d['cloud_url'], v.cloud_url)
      insert_mock.assert_called_with(
          trace.cloud_storage.PUBLIC_BUCKET,
          'test.html',
          os.path.join(tempdir, 'test.html'))
    finally:
      shutil.rmtree(tempdir)

  @mock.patch('telemetry.value.trace.cloud_storage.Insert')
  def testAsDictWhenTraceIsNotSerializedAndUploaded(self, insert_mock):
    v = trace.TraceValue(
        None, trace_data.CreateTraceDataFromRawData([{'test': 1}]),
        filename='a.html',
        # No local_dir is set.
        upload_bucket=trace.cloud_storage.PUBLIC_BUCKET)
    try:
      v.SerializeTraceData()
      v.UploadToCloud()
      d = v.AsDict()
      self.assertNotIn('file_path', d)
      self.assertEqual(d['cloud_url'], v.cloud_url)
      insert_mock.assert_called_with(
          trace.cloud_storage.PUBLIC_BUCKET,
          'a.html',
          mock.ANY)
    finally:
      v.CleanUp()


def _IsEmptyDir(path):
  return os.path.exists(path) and not os.listdir(path)


class NoLeakedTempfilesTests(unittest.TestCase):

  def setUp(self):
    super(NoLeakedTempfilesTests, self).setUp()
    self.temp_test_dir = tempfile.mkdtemp()
    self.actual_tempdir = trace.tempfile.tempdir
    trace.tempfile.tempdir = self.temp_test_dir

  def testNoLeakedTempFileOnImplicitCleanUp(self):
    with trace.TraceValue(
        None, trace_data.CreateTraceDataFromRawData([{'test': 1}])):
      pass
    self.assertTrue(_IsEmptyDir(self.temp_test_dir))

  def testNoLeakedTempFileWhenUploadingTrace(self):
    v = trace.TraceValue(
        None, trace_data.CreateTraceDataFromRawData([{'test': 1}]))
    v.CleanUp()
    self.assertTrue(_IsEmptyDir(self.temp_test_dir))

  def tearDown(self):
    super(NoLeakedTempfilesTests, self).tearDown()
    shutil.rmtree(self.temp_test_dir)
    trace.tempfile.tempdir = self.actual_tempdir
