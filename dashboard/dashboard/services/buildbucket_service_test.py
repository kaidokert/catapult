# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import unittest

import mock

from dashboard.services import buildbucket_service
from dashboard.common import utils

_BUILD_PARAMETERS = {
    'builder_name': 'dummy_builder',
    'properties': {
        'bisect_config': {}
    }
}


def _mock_uuid(): # pylint: disable=invalid-name
  return 'mock uuid'

class BuildbucketServiceTest(unittest.TestCase):

  def setUp(self):
    patcher = mock.patch('dashboard.services.request.RequestJson')
    self._request_json = patcher.start()
    self.addCleanup(patcher.stop)

    self._request_json.return_value = {'build': {'id': 'build id'}}

  def _AssertCorrectResponse(self, content):
    self.assertEqual(content, {'build': {'id': 'build id'}})

  def _AssertRequestMadeOnce(self, path, *args, **kwargs):
    self._request_json.assert_called_once_with(
        buildbucket_service.API_BASE_URL + path, *args, **kwargs)

  def _AssertRequestV2MadeOnce(self, path, *args, **kwargs):
    self._request_json.assert_called_once_with(
        buildbucket_service.API_BASE_URL2 + path, *args, **kwargs)

  def testPut(self):
    expected_body = {
        'bucket': 'bucket_name',
        'tags': ['buildset:foo'],
        'parameters_json': json.dumps(_BUILD_PARAMETERS, separators=(',', ':')),
    }
    response = buildbucket_service.Put('bucket_name', ['buildset:foo'],
                                       _BUILD_PARAMETERS)
    self._AssertCorrectResponse(response)
    self._AssertRequestMadeOnce('builds', method='PUT', body=expected_body)

  @mock.patch.object(utils, 'IsRunningBuildBucketV2', lambda: True)
  def testPutV2_badBucketName(self):
    self.assertRaises(ValueError, buildbucket_service.Put,
                      'invalid bucket string', [''], _BUILD_PARAMETERS)


  @mock.patch('uuid.uuid4', _mock_uuid)
  @mock.patch.object(utils, 'IsRunningBuildBucketV2', lambda: True)
  def testPutV2(self):
    expected_body = {
        'requestId': 'mock uuid',
        'builder': {
            'project': 'chrome',
            'bucket': 'bucket_name',
            'builder': _BUILD_PARAMETERS['builder_name'],
        },
        'tags': [{
            'key': 'bar',
            'value': 'foo'
        }],
        'properties': _BUILD_PARAMETERS.get('properties', {}),
    }
    response = buildbucket_service.Put('luci.chrome.bucket_name', ['bar:foo'],
                                       _BUILD_PARAMETERS)
    self._AssertCorrectResponse(response)
    self._AssertRequestV2MadeOnce(
        'ScheduleBuild', method='POST', body=expected_body)


  def testGetJobStatus(self):
    response = buildbucket_service.GetJobStatus('job_id')
    self._AssertCorrectResponse(response)
    self._AssertRequestMadeOnce('builds/job_id')

  @mock.patch.object(utils, 'IsRunningBuildBucketV2', lambda: True)
  def testGetJobStatusV2(self):
    response = buildbucket_service.GetJobStatus('job_id')
    self._AssertCorrectResponse(response)
    expected_body = json.dumps({
        'id': 'job_id',
    })
    self._AssertRequestV2MadeOnce('GetBuild', method='POST', body=expected_body)


class FakeJob(object):

  def GetBuildParameters(self):
    return _BUILD_PARAMETERS


if __name__ == '__main__':
  unittest.main()
