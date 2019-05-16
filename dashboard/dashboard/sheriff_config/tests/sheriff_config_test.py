# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Sheriff Config Service Tests

This test suite exercises the HTTP handlers from the Flask application defined
in the service module.
"""

# Support python3
from __future__ import absolute_import

import base64
import unittest
import json
import service
from apiclient.http import HttpMockSequence


class ValidationTest(unittest.TestCase):

  def setUp(self):
    with open('tests/config-discovery.json') as discovery_file:
      self.app = service.CreateApp({
          'environ': {
              'GAE_APPLICATION': 'chromeperf',
              'GAE_SERVICE': 'sheriff-config'
          },
          'http': HttpMockSequence([({
              'status': '200'
          }, discovery_file.read())])
      })
    self.client = self.app.test_client()

  def tearDown(self):
    self.client = None
    self.app = None

  def testServiceMetadata(self):
    # We want to ensure that we can get a valid service metadata description
    # which points to a validation endpoint. We're implementing the protocol
    # buffer definition for a ServiceDynamicMetadata without an explicit
    # dependency on the proto definition.
    response = self.client.get('/service-metadata')

    # First, ensure that the response is valid json.
    config = json.loads(response.data)

    # Then, ensure that we have the validation sub-object.
    self.assertIn('validation', config)
    self.assertIn('url', config['validation'])
    self.assertEquals(
        config['validation']['url'],
        'https://sheriff-config-dot-chromeperf.appspot.com/validate')

  def testValidationPropagatesError(self):
    response = self.client.post(
        '/validate',
        json={
            'config_set':
                'project:some-project',
            'path':
                'infra/config/chromeperf-sheriff.cfg',
            'content':
                base64.standard_b64encode(
                    bytearray(
                        json.dumps({'subscriptions': [{
                            'name': 'Name'
                        }]}), 'utf-8')).decode('utf-8')
        })

    self.assertEquals(response.status_code, 200)
    response_proto = response.get_json()
    self.assertIn('messages', response_proto)
    self.assertGreater(len(response_proto['messages']), 0)
    self.assertRegexpMatches(response_proto['messages'][0].get('text'),
                             'notification_email')

  def testValidationSucceedsSilently(self):
    response = self.client.post(
        '/validate',
        json={
            'config_set':
                'project:some-project',
            'path':
                'infra/config/chromeperf-sheriff.cfg',
            'content':
                base64.standard_b64encode(
                    bytearray(
                        json.dumps({
                            'subscriptions': [{
                                'name':
                                    'Release Team',
                                'notification_email':
                                    'release-team@example.com',
                                'bug_labels': ['release-blocker'],
                                'bug_components': ['Sample>Component'],
                                'patterns': [{
                                    'glob': 'project/**'
                                }]
                            }, {
                                'name':
                                    'Memory Team',
                                'notification_email':
                                    'memory-team@example.com',
                                'bug_labels': ['memory-regressions'],
                                'patterns': [{
                                    'regex': '^project/.*memory_.*$'
                                }],
                                'anomaly_configs': [{
                                    'min_relative_change':
                                        0.01,
                                    'patterns': [{
                                        'regex':
                                            '^project/platform/.*/memory_peak$'
                                    }]
                                }]
                            }]
                        }), 'utf-8')).decode('utf-8')
        })
    self.assertEquals(response.status_code, 200)
    response_proto = response.get_json()
    self.assertNotIn('messages', response_proto)


class LuciPollingTest(unittest.TestCase):

  def setUp(self):
    with open('tests/config-discovery.json') as discovery_file:
      self.discovery_file = discovery_file.read()

  def testPollAndMatch(self):
    with open(
        'tests/sample-configs-get_project_configs.json') as sample_config_file:
      sample_config = sample_config_file.read()
    # FIXME: Mock/Fake the Datastore Client API
    app = service.CreateApp({
        'environ': {
            'GAE_APPLICATION': 'chromeperf',
            'GAE_SERVICE': 'sheriff-config',
        },
        'http':
            HttpMockSequence([({
                'status': '200'
            }, self.discovery_file), ({
                'status': '200'
            }, sample_config)]),
    })
    client = app.test_client()
    response = client.get('/update-configs')
    self.assertEquals(response.status_code, 200)
    response = client.post(
        '/match-subscriptions',
        json={
            'path': 'Master/Bot/Test/Metric/Something',
            'stat': 'PCT_99',
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'Something'],
            }
        })
    self.assertEquals(response.status_code, 200)
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
                    'patterns': [{'glob'}]
                }
            }]
        })
