#!/usr/bin/env python
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

from services import request


class Api(object):
  SERVICE_URL = 'https://chromeperf.appspot.com/api'

  def __init__(self, credentials):
    self._credentials = credentials

  def Request(self, endpoint, **kwargs):
    """Send a request to some isolate service endpoint."""
    kwargs.setdefault('credentials', self._credentials)
    kwargs.setdefault('method', 'POST')
    return json.loads(request.Request(self.SERVICE_URL + endpoint, **kwargs))

  def Describe(self, test_suite):
    return self.Request('/describe/%s' % test_suite)
