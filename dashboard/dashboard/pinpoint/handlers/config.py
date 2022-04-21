# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from dashboard.api import api_request_handler
from dashboard.api.api_handler_decorator import request_handler_decorator_factory as handler_decorator
from dashboard.common import bot_configurations
from dashboard.pinpoint.dispatcher_py3 import APP
from flask import make_response, request

def _CheckUser():
  pass

@APP.route('/api/config', methods=['POST'])
@handler_decorator(_CheckUser)
def configHandlerPost():
  return {'configurations': bot_configurations.List()}