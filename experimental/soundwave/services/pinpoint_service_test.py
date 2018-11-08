#!/usr/bin/env python
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import mock

from services import pinpoint_service


class TestPinpointApi(unittest.TestCase):
  def setUp(self):
    self.get_user_email = mock.patch(
        'services.luci_auth.GetUserEmail').start()
    self.get_user_email.return_value = 'user@example.com'
    self.mock_request = mock.patch('services.request.Request').start()
    self.mock_request.return_value = '"OK"'
    self.api = pinpoint_service.Api()

  def tearDown(self):
    mock.patch.stopall()

  def testJob(self):
    self.assertEqual(self.api.Job('1234'), 'OK')
    self.mock_request.assert_called_once_with(
        self.api.SERVICE_URL + '/job/1234', params=[], use_auth=True)

  def testJob_withState(self):
    self.assertEqual(self.api.Job('1234', with_state=True), 'OK')
    self.mock_request.assert_called_once_with(
        self.api.SERVICE_URL + '/job/1234', params=[('o', 'STATE')],
        use_auth=True)

  def testJobs(self):
    self.mock_request.return_value = '["job1", "job2", "job3"]'
    self.assertEqual(self.api.Jobs(), ['job1', 'job2', 'job3'])
    self.mock_request.assert_called_once_with(
        self.api.SERVICE_URL + '/jobs', use_auth=True)

  def testNewJob(self):
    self.assertEqual(self.api.NewJob(
        name='test_job', configuration='some_config'), 'OK')
    self.mock_request.assert_called_once_with(
        self.api.SERVICE_URL + '/new', method='POST',
        data={'name': 'test_job', 'configuration': 'some_config',
              'user': 'user@example.com'},
        use_auth=True)
