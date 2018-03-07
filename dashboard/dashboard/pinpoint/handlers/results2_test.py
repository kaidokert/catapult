# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import mock

import webapp2
import webtest

from dashboard.common import testing_common
from dashboard.pinpoint.handlers import results2


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


class _Results2Test(testing_common.TestCase):

  def setUp(self):
    super(_Results2Test, self).setUp()

    app = webapp2.WSGIApplication([
        webapp2.Route(r'/results2/<job_id>', results2.Results2),
    ])
    self.testapp = webtest.TestApp(app)
    self.testapp.extra_environ.update({'REMOTE_ADDR': 'remote_ip'})

    self._job_from_id = mock.MagicMock()
    patcher = mock.patch.object(results2.job_module, 'JobFromId',
                                self._job_from_id)
    self.addCleanup(patcher.stop)
    patcher.start()

  def _SetJob(self, job):
    self._job_from_id.return_value = job


@mock.patch.object(results2.cloudstorage, 'listbucket')
class Results2TestGetTest(_Results2Test):

  def testGet_InvalidJob(self, mock_cloudstorage):
    mock_cloudstorage.return_value = []

    self._SetJob(None)
    response = self.testapp.get('/results2/123', status=400)
    self.assertIn('Error', response.body)

  def testGet_Cached_ReturnsResult(self, mock_cloudstorage):
    mock_cloudstorage.return_value = ['foo']

    self._SetJob(None)
    response = self.testapp.get('/results2/456')
    result = json.loads(response.body)
    self.assertEqual('complete', result['status'])
    self.assertEqual(
        'https://storage.cloud.google.com/chromeperf.appspot.com/results2/'
        '456.html',
        result['url'])

  def testGet_Uncached_SchedulesGenerate(self, mock_cloudstorage):
    mock_cloudstorage.return_value = []

    self._SetJob(_JobStub(_JOB_WITH_DIFFERENCES))
    response = self.testapp.get('/results2/789')
    result = json.loads(response.body)
    self.assertEqual('pending', result['status'])


@mock.patch.object(results2, 'open', mock.mock_open(read_data='fake_viewer'),
                   create=True)
class PostTest(_Results2Test):

  @mock.patch.object(results2, '_FetchHistogramsDataFromJobData',
                     mock.MagicMock(return_value=['a', 'b']))
  @mock.patch.object(results2, '_GcsFileStream', mock.MagicMock())
  @mock.patch.object(results2.render_histograms_viewer,
                     'RenderHistogramsViewer')
  def testPost_Renders(self, mock_render):
    self._SetJob(_JobStub(_JOB_NO_DIFFERENCES))
    self.testapp.post('/results2/123')

    mock_render.assert_called_with(
        ['a', 'b'], mock.ANY, reset_results=True, vulcanized_html='fake_viewer')

    results = results2.JobCachedResults2.query().fetch()
    self.assertEqual(1, len(results))

  @mock.patch.object(results2.read_value, '_RetrieveOutputJson',
                     mock.MagicMock(return_value=['a']))
  @mock.patch.object(results2, '_GcsFileStream', mock.MagicMock())
  def testPost_InvalidJob(self):
    self._SetJob(None)
    response = self.testapp.post('/results2/123')
    self.assertIn('Error', response.body)


@mock.patch.object(results2.read_value, '_RetrieveOutputJson',
                   mock.MagicMock(return_value=['a']))
class FetchHistogramsTest(_Results2Test):
  def testGet_WithNoDifferences(self):
    self._SetJob(_JobStub(_JOB_NO_DIFFERENCES))
    fetch = results2._FetchHistogramsDataFromJobData('123')
    self.assertEqual(['a', 'a', 'a', 'a'], [f for f in fetch])

  def testGet_WithDifferences(self):
    self._SetJob(_JobStub(_JOB_WITH_DIFFERENCES))
    fetch = results2._FetchHistogramsDataFromJobData('123')
    self.assertEqual(['a', 'a', 'a'], [f for f in fetch])

  def testGet_MissingExecutions(self):
    self._SetJob(_JobStub(_JOB_MISSING_EXECUTIONS))
    fetch = results2._FetchHistogramsDataFromJobData('123')
    self.assertEqual(['a', 'a'], [f for f in fetch])


class _JobStub(object):

  def __init__(self, job_dict):
    self._job_dict = job_dict

  def ScheduleResults2Generation(self):
    return 'pending'

  def AsDict(self, options=None):
    del options
    return self._job_dict
