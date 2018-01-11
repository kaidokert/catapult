# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock
import unittest
import urllib2

import py_utils

from telemetry import decorators
from telemetry.internal.util import binary_manager
from telemetry.internal.util import webpagereplay_go_server


class WebPageReplayGoServerTest(unittest.TestCase):

  def setUp(self):
    self.archive_path = binary_manager.FetchPath(
        'example_domain_wpr_go_archive',
        py_utils.GetHostArchName(),
        py_utils.GetHostOsName())

  @decorators.Disabled('chromeos')  # crbug.com/750323
  def testSmokeStartingWebPageReplayGoServer(self):
    with webpagereplay_go_server.ReplayServer(
        self.archive_path, replay_host='127.0.0.1', http_port=0, https_port=0,
        replay_options=[]) as server:
      self.assertIsNotNone(server.http_port)
      self.assertIsNotNone(server.https_port)

      # Make sure that we can establish connection to HTTP port.
      req = urllib2.Request(
          'http://www.example.com/', origin_req_host='127.0.0.1')
      r = urllib2.urlopen(req)
      self.assertEquals(r.getcode(), 200)

      # Make sure that we can establish connection to HTTPS port.
      req = urllib2.Request(
          'https://www.example.com/', origin_req_host='127.0.0.1')
      r = urllib2.urlopen(req)
      self.assertEquals(r.getcode(), 200)

  @mock.patch('py_utils.atexit_with_log.Register')
  def testKillingWebPageReplayProcessUponStartupFailure(
      self, atexit_with_log_register_patch):
    atexit_with_log_register_patch.side_effect = KeyError('Bang!')
    with self.assertRaises(webpagereplay_go_server.ReplayNotStartedError):
      server = webpagereplay_go_server.ReplayServer(
          self.archive_path, replay_host='127.0.0.1', http_port=0, https_port=0,
          replay_options=[])
      server.StartServer()

    # Ensure replay process is probably cleaned up after StartServer crashed.
    self.assertIsNone(server.replay_process)
