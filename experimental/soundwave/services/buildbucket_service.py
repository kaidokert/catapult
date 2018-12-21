#!/usr/bin/env python
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Make requests to the Buildbucket RPC API.

For more details on the API see: go/buildbucket-rpc
"""

import json
import urllib

from services import request

SERVICE_URL = 'https://cr-buildbucket.appspot.com/prpc/buildbucket.v2.Builds'


def Request(endpoint, **kwargs):
  """Send a request to some buildbucket service endpoint."""
  kwargs.setdefault('use_auth', True)
  kwargs.setdefault('method', 'POST')
  kwargs.setdefault('content_type', 'json')
  kwargs.setdefault('accept', 'jsonp')
  return request.Request(SERVICE_URL + endpoint, **kwargs)


def GetBuild(project, bucket, builder, build_number):
  return Request('/GetBuild', data={
      'builder': {
          'project': project,
          'bucket': bucket,
          'builder': builder,
      },
      'buildNumber': build_number
  })


if __name__ == '__main__':
  from services import luci_auth
  luci_auth.CheckLoggedIn()
  print GetBuild('chrome', 'ci', 'android-pixel2-perf', 1762)
