# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from telemetry.core import exceptions
from telemetry.internal.backends.chrome_inspector import devtools_http


class DevToolsHttpTest(unittest.TestCase):

  def testUrlError(self):
    with self.assertRaises(exceptions.DevToolsClientUrlError):
      devtools_http.DevToolsHttp(1000).Request('')

  def testSocketError(self):
    with self.assertRaises(exceptions.DevToolsClientConnectionError) as e:
      devtools_http.DevToolsHttp(1000).Request('')
      self.assertnotisinstance(e, exceptions.DevToolsClientUrlError)
