# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""E2E Tests for the Sheriff Config Service

This test assumes a number of things:

  - We are running against an emulator for the datastore service.
  - We are mocking the luci-config service calls and responses.

We typically run this in the testing Docker container.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import service
import unittest
from apiclient.http import HttpMockSequence
from google.cloud import datastore
from google.auth import credentials


class LuciPollingTest(unittest.TestCase):

  def setUp(self):
    with open('tests/config-discovery.json') as discovery_file:
      self.discovery_file = discovery_file.read()
    with open(
        'tests/sample-configs-get_project_configs.json') as sample_config_file:
      self.sample_config = sample_config_file.read()
    self.app = service.CreateApp({
        'environ': {
            'GAE_APPLICATION': 'chromeperf',
            'GAE_SERVICE': 'sheriff-config',
        },
        'datastore_client':
            datastore.Client(
                credentials=credentials.AnonymousCredentials(),
                project='chromeperf'),
        'http':
            HttpMockSequence([({
                'status': '200'
            }, self.discovery_file), ({
                'status': '200'
            }, self.sample_config)]),
    })

  def tearDown(self):
    self.app = None

  def testPollAndMatch(self):
    client = self.app.test_client()
    response = client.get('/configs/update')
    self.assertEqual(response.status_code, 200)
    response = client.post(
        '/subscriptions/match',
        json={
            'path': 'Master/Bot/Test/Metric/Something',
            'stats': ['PCT_99'],
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'Something'],
            }
        })
    self.assertEqual(response.status_code, 200)
    response_proto = response.get_json()
    self.assertDictEqual(
        response_proto, {
            'subscriptions': [{
                'config_set': 'projects/other_project',
                'revision': '0123456789abcdff',
                'subscription': {
                    'name': 'Expected 1',
                    'notification_email': 'expected-1@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'patterns': [{
                        'glob': 'Master/Bot/Test/Metric/Something'
                    }]
                }
            }]
        })

  def testPollAndMatchMultiple(self):
    client = self.app.test_client()
    response = client.get('/configs/update')
    self.assertEqual(response.status_code, 200)
    response = client.post(
        '/subscriptions/match',
        json={
            'path': 'project/platform/not-important/memory_peak',
            'stats': ['PCT_99'],
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'Something'],
            }
        })
    self.assertEqual(response.status_code, 200)
    response_proto = response.get_json()
    self.assertDictEqual(
        response_proto, {
            'subscriptions': [{
                'config_set': 'projects/project',
                'revision': '0123456789abcdef',
                'subscription': {
                    'name': 'Config 1',
                    'notification_email': 'config-1@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'patterns': [{
                        'glob': 'project/**'
                    }]
                }
            }, {
                'config_set': 'projects/project',
                'revision': '0123456789abcdef',
                'subscription': {
                    'name': 'Config 2',
                    'notification_email': 'config-2@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'patterns': [{
                        'regex': '^project/platform/.*/memory_peak$'
                    }]
                }
            }]
        })
