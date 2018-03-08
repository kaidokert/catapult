# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock

import webapp2
import webtest

from dashboard.common import testing_common
from dashboard.pinpoint.handlers import results2
from dashboard.pinpoint.models.results2 import Results2Error


class _Results2Test(testing_common.TestCase):

  def setUp(self):
    super(_Results2Test, self).setUp()

    app = webapp2.WSGIApplication([
        webapp2.Route(r'/results2/<job_id>', results2.Results2),
        webapp2.Route(
            r'/generate-results2/<job_id>', results2.Results2Generator),
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


@mock.patch.object(results2.results2, 'GetOrScheduleResults2')
class Results2GetTest(_Results2Test):

  def testGet_CallsGetOrScheduleResults2(self, mock_schedule):
    mock_schedule.return_value = ('', '')
    self._SetJob(_JobStub('456'))

    self.testapp.get('/results2/456')
    self.assertTrue(mock_schedule.called)


@mock.patch.object(results2.results2, 'GenerateResults2')
class Results2GeneratorPostTest(_Results2Test):

  def testGet_CallsGenerate(self, mock_generate):
    self._SetJob(_JobStub('789'))
    self.testapp.post('/generate-results2/789')
    self.assertTrue(mock_generate.called)

  def testGet_ReturnsError(self, mock_generate):
    mock_generate.side_effect = Results2Error('foo')
    self._SetJob(_JobStub('101112'))

    response = self.testapp.post('/generate-results2/101112')
    self.assertIn('foo', response.body)


class _JobStub(object):

  def __init__(self, job_id):
    self.job_id = job_id
