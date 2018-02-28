# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import mock
import unittest

import webapp2
import webtest

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from dashboard.pinpoint.handlers import results2
from dashboard.pinpoint.models import job as job_module


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


class _Results2Test(unittest.TestCase):

  def setUp(self):
    app = webapp2.WSGIApplication([
        webapp2.Route(r'/results2/<job_id>', results2.Results2),
    ])
    self.testapp = webtest.TestApp(app)
    self.testapp.extra_environ.update({'REMOTE_ADDR': 'remote_ip'})

    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()
    ndb.get_context().clear_cache()

    self._job_from_id = mock.MagicMock()
    patcher = mock.patch.object(results2.job_module, 'JobFromId',
                                self._job_from_id)
    self.addCleanup(patcher.stop)
    patcher.start()

  def _SetJob(self, job):
    self._job_from_id.return_value = job


class GetTest(_Results2Test):

  @mock.patch.object(results2.cloudstorage, 'listbucket',
                     mock.MagicMock(return_value=[]))
  def testGet_InvalidJob(self):
    self._SetJob(None)
    response = self.testapp.get('/results2/123', status=400)
    self.assertIn('Error', response.body)

  @mock.patch.object(results2.cloudstorage, 'listbucket',
                     mock.MagicMock(return_value=['foo']))
  def testGet_Cached_ReturnsResult(self):
    response = self.testapp.get('/results2/123')
    result = json.loads(response.body)
    self.assertEqual('complete', result['status'])
    self.assertEqual(
        'https://storage.cloud.google.com/chromeperf.appspot.com/results2/'
        '123.html',
        result['url'])

  @mock.patch.object(results2.cloudstorage, 'listbucket',
                     mock.MagicMock(return_value=[]))
  def testGet_Uncached_SchedulesGenerate(self):
    self._SetJob(_JobStub(_JOB_WITH_DIFFERENCES))
    response = self.testapp.get('/results2/123')
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

    results = job_module.JobCachedResults2.query().fetch()
    self.assertEqual(1, len(results))

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
    self.assertEqual(
        ['e26a40a0d4', 'e26a40a0d4', 'e26a40a0d4', 'e26a40a0d4'],
        fetch.isolate_hashes)

  def testGet_WithDifferences(self):
    self._SetJob(_JobStub(_JOB_WITH_DIFFERENCES))
    fetch = results2._FetchHistogramsDataFromJobData('123')
    self.assertEqual(
        ['e26a40a0d4', 'e26a40a0d4', 'e26a40a0d4'], fetch.isolate_hashes)

  def testGet_MissingExecutions(self):
    self._SetJob(_JobStub(_JOB_MISSING_EXECUTIONS))
    fetch = results2._FetchHistogramsDataFromJobData('123')
    self.assertEqual(['e26a40a0d4', 'e26a40a0d4'], fetch.isolate_hashes)


# pylint: disable=invalid-name

class _StreamStub(object):

  def __init__(self):
    self.content = ''

  def close(self):
    pass

  def seek(self, _):
    pass

  def truncate(self):
    pass

  def write(self, content):
    self.content += content

# pylint: enable=invalid-name


class _JobStub(object):

  def __init__(self, job_dict):
    self._job_dict = job_dict

  def ScheduleResults2Generation(self):
    return 'pending'

  def AsDict(self, options=None):
    del options
    return self._job_dict
