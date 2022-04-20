# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import six

from dashboard.api import api_request_handler
from dashboard.api.api_handler_decorator import request_handler_decorator_factory as handler_decorator
from dashboard.pinpoint.models import change
from dashboard.pinpoint.dispatcher_py3 import APP
from flask import request

def _CheckUser():
  pass

@APP.route('/api/commit', methods=['POST'])
@handler_decorator(_CheckUser)
def commitHandlerPost():
  repository = request.args.get('repository', 'chromium')
  git_hash = request.args.get('git_hash')
  try:
    c = change.Commit.FromDict({
        'repository': repository,
        'git_hash': git_hash,
    })
    return c.AsDict()
  except KeyError as e:
    six.raise_from(
        api_request_handler.BadRequestError('Unknown git hash: %s' %
                                            git_hash), e)