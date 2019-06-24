# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest

import mock

from telemetry.internal.results import story_run
from telemetry.internal.util import file_handle
from telemetry.story import shared_state
from telemetry import story as story_module
from telemetry.value import improvement_direction
from telemetry.value import scalar

from py_utils import tempfile_ext


# splitdrive returns '' on systems which don't have drives, like linux.
ROOT_CHAR = os.path.splitdrive(__file__)[0] + os.sep
def _abs_join(*args):
  """Helper to do a path join that's an absolute path."""
  return ROOT_CHAR + os.path.join(*args)


class StoryRunTest(unittest.TestCase):
  def setUp(self):
    self.story = story_module.Story(shared_state.SharedState, name='foo')

  def testStoryRunFailed(self):
    run = story_run.StoryRun(self.story)
    run.SetFailed('abc')
    self.assertFalse(run.ok)
    self.assertTrue(run.failed)
    self.assertFalse(run.skipped)
    self.assertEquals(run.failure_str, 'abc')

    run = story_run.StoryRun(self.story)
    run.AddValue(scalar.ScalarValue(
        self.story, 'a', 's', 1,
        improvement_direction=improvement_direction.UP))
    run.SetFailed('something is wrong')
    self.assertFalse(run.ok)
    self.assertTrue(run.failed)
    self.assertFalse(run.skipped)
    self.assertEquals(run.failure_str, 'something is wrong')

  def testStoryRunSkipped(self):
    run = story_run.StoryRun(self.story)
    run.SetFailed('oops')
    run.Skip('test', is_expected=True)
    self.assertFalse(run.ok)
    self.assertFalse(run.failed)
    self.assertTrue(run.skipped)
    self.assertTrue(run.is_expected)
    self.assertEquals(run.failure_str, 'oops')

    run = story_run.StoryRun(self.story)
    run.AddValue(scalar.ScalarValue(
        self.story, 'a', 's', 1,
        improvement_direction=improvement_direction.UP))
    run.Skip('test', is_expected=False)
    self.assertFalse(run.ok)
    self.assertFalse(run.failed)
    self.assertTrue(run.skipped)
    self.assertFalse(run.is_expected)
    self.assertEquals(run.failure_str, None)

  def testStoryRunSucceeded(self):
    run = story_run.StoryRun(self.story)
    self.assertTrue(run.ok)
    self.assertFalse(run.failed)
    self.assertFalse(run.skipped)
    self.assertEquals(run.failure_str, None)

    run = story_run.StoryRun(self.story)
    run.AddValue(scalar.ScalarValue(
        self.story, 'a', 's', 1,
        improvement_direction=improvement_direction.UP))
    self.assertTrue(run.ok)
    self.assertFalse(run.failed)
    self.assertFalse(run.skipped)
    self.assertEquals(run.failure_str, None)


  @mock.patch('telemetry.internal.results.story_run.time')
  def testAsDict(self, time_module):
    time_module.time.side_effect = [1234567890.987,
                                    1234567900.987]
    run = story_run.StoryRun(self.story)
    run.AddValue(scalar.ScalarValue(
        self.story, 'a', 's', 1,
        improvement_direction=improvement_direction.UP))
    run.Finish()
    self.assertEquals(
        run.AsDict(),
        {
            'testResult': {
                'testName': 'foo',
                'status': 'PASS',
                'isExpected': True,
                'startTime': '2009-02-13T23:31:30.987000Z',
                'runDuration': '10.00s'
            }
        }
    )

  def testCreateArtifact(self):
    with tempfile_ext.NamedTemporaryDirectory() as tempdir:
      run = story_run.StoryRun(self.story, tempdir)
      with run.CreateArtifact('logs') as log_file:
        log_file.write('hi\n')

      filename = run.GetArtifact('logs').local_path
      with open(filename) as f:
        self.assertEqual(f.read(), 'hi\n')

  def testCaptureArtifact(self):
    with tempfile_ext.NamedTemporaryDirectory() as tempdir:
      run = story_run.StoryRun(self.story, tempdir)
      with run.CaptureArtifact('logs') as log_file_name:
        with open(log_file_name, 'w') as log_file:
          log_file.write('hi\n')

      filename = run.GetArtifact('logs').local_path
      with open(filename) as f:
        self.assertEqual(f.read(), 'hi\n')

  @mock.patch('telemetry.internal.results.story_run.shutil.move')
  @mock.patch('telemetry.internal.results.story_run.os.makedirs')
  def testAddArtifactBasic(self, make_patch, move_patch):
    run = story_run.StoryRun(self.story, _abs_join('foo'))

    run.AddArtifact('name', _abs_join('bar.log'))
    move_patch.assert_called_with(_abs_join('bar.log'),
                                  _abs_join('foo', 'artifacts', 'name'))
    make_patch.assert_called_with(_abs_join('foo', 'artifacts'))

    self.assertEqual(run.GetArtifact('name').local_path,
                     _abs_join('foo', 'artifacts', 'name'))

  @mock.patch('telemetry.internal.results.story_run.shutil.move')
  @mock.patch('telemetry.internal.results.story_run.os.makedirs')
  def testAddArtifactNested(self, make_patch, move_patch):
    run = story_run.StoryRun(self.story, _abs_join('foo'))

    run.AddArtifact('dir/name', _abs_join('bar.log'))
    move_patch.assert_called_with(_abs_join('bar.log'),
                                  _abs_join('foo', 'artifacts', 'dir', 'name'))
    make_patch.assert_has_calls([
        mock.call(_abs_join('foo', 'artifacts')),
        mock.call(_abs_join('foo', 'artifacts', 'dir')),
    ])

    self.assertEqual(run.GetArtifact('dir/name').local_path,
                     _abs_join('foo', 'artifacts', 'dir', 'name'))

  @mock.patch('telemetry.internal.results.story_run.shutil.move')
  @mock.patch('telemetry.internal.results.story_run.os.makedirs')
  def testAddArtifactFileHandle(self, make_patch, move_patch):
    run = story_run.StoryRun(self.story, _abs_join('foo'))

    run.AddArtifact('name', file_handle.FromFilePath(
        _abs_join('bar.log')))
    move_patch.assert_called_with(_abs_join('bar.log'),
                                  _abs_join('foo', 'artifacts', 'name'))
    make_patch.assert_called_with(_abs_join('foo', 'artifacts'))

    self.assertEqual(run.GetArtifact('name').local_path,
                     _abs_join('foo', 'artifacts', 'name'))

  @mock.patch('telemetry.internal.results.story_run.shutil.move')
  @mock.patch('telemetry.internal.results.story_run.os.makedirs')
  def testIterArtifacts(self, make_patch, move_patch):
    del make_patch  # unused
    del move_patch  # unused
    run = story_run.StoryRun(self.story, _abs_join('foo'))

    run.AddArtifact('log/log1', _abs_join('log.log'))
    run.AddArtifact('trace/trace1', _abs_join('trace.json'))
    run.AddArtifact('trace/trace2', _abs_join('trace.pb'))

    all_artifacts = list(run.IterArtifacts())
    self.assertEqual(3, len(all_artifacts))

    logs = list(run.IterArtifacts('log'))
    self.assertEqual(1, len(logs))

    traces = list(run.IterArtifacts('trace'))
    self.assertEqual(2, len(traces))
