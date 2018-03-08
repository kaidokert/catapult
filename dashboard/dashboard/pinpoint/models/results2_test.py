# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock
import unittest

from google.appengine.api import taskqueue

from dashboard.common import testing_common
from dashboard.pinpoint.models import results2


_ATTEMPT_DATA = {
    "executions": [{"result_arguments": {"isolate_hash": "e26a40a0d4"}}]
}


_JOB_NO_DIFFERENCES = {
    "changes": [{}, {}, {}, {}],
    "quests": ["Test"],
    "comparisons": ["same", "same", "same"],
    "attempts": [
        [_ATTEMPT_DATA],
        [_ATTEMPT_DATA],
        [_ATTEMPT_DATA],
        [_ATTEMPT_DATA],
    ],
}


_JOB_WITH_DIFFERENCES = {
    "changes": [{}, {}, {}, {}],
    "quests": ["Test"],
    "comparisons": ["same", "different", "different"],
    "attempts": [
        [_ATTEMPT_DATA],
        [_ATTEMPT_DATA],
        [_ATTEMPT_DATA],
        [_ATTEMPT_DATA],
    ],
}


_JOB_MISSING_EXECUTIONS = {
    "changes": [{}, {}],
    "quests": ["Test"],
    "comparisons": ["same"],
    "attempts": [
        [_ATTEMPT_DATA, {"executions": []}],
        [{"executions": []}, _ATTEMPT_DATA],
    ],
}


@mock.patch.object(results2.cloudstorage, 'listbucket')
class GetOrScheduleResults2Test(unittest.TestCase):

  def testGetOrScheduleResults2_InvalidJob_Raises(self, _):
    with self.assertRaises(results2.Results2Error):
      results2.GetOrScheduleResults2(None)

  def testGetOrScheduleResults2_Cached_ReturnsResult(self, mock_cloudstorage):
    mock_cloudstorage.return_value = ['foo']

    job = _JobStub(_JOB_WITH_DIFFERENCES, '123', None)
    status, url = results2.GetOrScheduleResults2(job)

    self.assertEqual('complete', status)
    self.assertEqual(
        'https://storage.cloud.google.com/chromeperf.appspot.com/results2/'
        '%s.html' % job.job_id,
        url)

  @mock.patch.object(results2, 'ScheduleResults2Generation', mock.MagicMock())
  def testGetOrScheduleResults2_Uncached_SchedulesGenerate(
      self, mock_cloudstorage):
    mock_cloudstorage.return_value = []

    job = _JobStub(_JOB_WITH_DIFFERENCES, '123', None)
    status, _ = results2.GetOrScheduleResults2(job)

    self.assertEqual('pending', status)

  @mock.patch.object(results2, 'ScheduleResults2Generation',
                     mock.MagicMock(side_effect=taskqueue.TombstonedTaskError))
  def testGetOrScheduleResults2_Uncached_FailedPreviously(
      self, mock_cloudstorage):
    mock_cloudstorage.return_value = []

    job = _JobStub(_JOB_WITH_DIFFERENCES, '123', None)
    status, _ = results2.GetOrScheduleResults2(job)

    self.assertEqual('failed', status)

  @mock.patch.object(
      results2, 'ScheduleResults2Generation',
      mock.MagicMock(side_effect=taskqueue.TaskAlreadyExistsError))
  def testGetOrScheduleResults2_Uncached_AlreadyRunning(
      self, mock_cloudstorage):
    mock_cloudstorage.return_value = []

    job = _JobStub(_JOB_WITH_DIFFERENCES, '123', None)
    status, _ = results2.GetOrScheduleResults2(job)

    self.assertEqual('pending', status)


@mock.patch.object(results2, 'open', mock.mock_open(read_data='fake_viewer'),
                   create=True)
class GenerateResults2Test(testing_common.TestCase):

  @mock.patch.object(results2, '_FetchHistogramsDataFromJobData',
                     mock.MagicMock(return_value=['a', 'b']))
  @mock.patch.object(results2, '_GcsFileStream', mock.MagicMock())
  @mock.patch.object(results2.render_histograms_viewer,
                     'RenderHistogramsViewer')
  def testPost_Renders(self, mock_render):
    job = _JobStub(_JOB_NO_DIFFERENCES, '123', None)
    results2.GenerateResults2(job)

    mock_render.assert_called_with(
        ['a', 'b'], mock.ANY, reset_results=True, vulcanized_html='fake_viewer')

    results = results2.CachedResults2.query().fetch()
    self.assertEqual(1, len(results))

  @mock.patch.object(results2.read_value, '_RetrieveOutputJson',
                     mock.MagicMock(return_value=['a']))
  @mock.patch.object(results2, '_GcsFileStream', mock.MagicMock())
  def testPost_InvalidJob(self):
    with self.assertRaises(results2.Results2Error):
      results2.GenerateResults2(None)


@mock.patch.object(results2.read_value, '_RetrieveOutputJson',
                   mock.MagicMock(return_value=['a']))
class FetchHistogramsTest(unittest.TestCase):
  def testGet_WithNoDifferences(self):
    job = _JobStub(_JOB_NO_DIFFERENCES, '123', None)
    fetch = results2._FetchHistogramsDataFromJobData(job)
    self.assertEqual(['a', 'a', 'a', 'a'], [f for f in fetch])

  def testGet_WithDifferences(self):
    job = _JobStub(_JOB_WITH_DIFFERENCES, '123', None)
    fetch = results2._FetchHistogramsDataFromJobData(job)
    self.assertEqual(['a', 'a', 'a'], [f for f in fetch])

  def testGet_MissingExecutions(self):
    job = _JobStub(_JOB_MISSING_EXECUTIONS, '123', None)
    fetch = results2._FetchHistogramsDataFromJobData(job)
    self.assertEqual(['a', 'a'], [f for f in fetch])


class _TaskStub(object):
  pass


class _JobStub(object):

  def __init__(self, job_dict, job_id, task):
    self._job_dict = job_dict
    self.job_id = job_id
    self.task = task

  def AsDict(self, options=None):
    del options
    return self._job_dict
