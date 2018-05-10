# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Functions for interfacing with Gerrit, a web-based code review tool for Git.

API doc: https://gerrit-review.googlesource.com/Documentation/rest-api.html
"""

import json
import logging

from dashboard.common import utils
from dashboard.services import request


OAUTH_SCOPE_GERRIT = 'https://www.googleapis.com/auth/gerritcodereview'

def GetChange(server_url, change_id, fields=None):
  url = '%s/changes/%s' % (server_url, change_id)
  return request.RequestJson(url, o=fields)

def PostChangeComment(server_url, change_id, comment):
  url = '%s/changes/%s/current/review' % (server_url, change_id)
  content = request.Request(
      url,
      method='POST',
      body=json.dumps({'message': comment}),
      use_cache=False,
      use_auth=True,
      scope=[OAUTH_SCOPE_GERRIT, utils.EMAIL_SCOPE])
  logging.Log(content)
