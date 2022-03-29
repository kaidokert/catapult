# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import logging
import re
import traceback

from dashboard.api import api_auth_flask
from dashboard.common import utils
from flask import make_response, request

_ALLOWED_ORIGINS = [
    'chromeperf.appspot.com',
    'pinpoint-dot-chromeperf.appspot.com',
    'chromiumdash.appspot.com',
    'chromiumdash-staging.googleplex.com',
]
if utils.IsStagingEnvironment():
  _ALLOWED_ORIGINS = [
      'chromeperf-stage.uc.r.appspot.com',
      'pinpoint-dot-chromeperf-stage.uc.r.appspot.com',
      'pinpoint-py3-dot-chromeperf-stage.uc.r.appspot.com',
  ]


class BadRequestError(Exception):
  pass


class ForbiddenError(Exception):

  def __init__(self):
    super(ForbiddenError, self).__init__('Access denied')


class NotFoundError(Exception):

  def __init__(self):
    super(NotFoundError, self).__init__('Not found')


def RequestHandlerDecoratorFactory(user_checker):

  def RequestHandlerDecorator(request_handler):

    def Wrapper():
      try:
        user_checker()
      except api_auth_flask.NotLoggedInError as e:
        return _WriteErrorMessage(str(e), 401)
      except api_auth_flask.OAuthError as e:
        return _WriteErrorMessage(str(e), 403)
      except ForbiddenError as e:
        return _WriteErrorMessage(str(e), 403)
      # Allow oauth.Error to manifest as HTTP 500.

      try:
        results = request_handler()
      except NotFoundError as e:
        return _WriteErrorMessage(str(e), 404)
      except (BadRequestError, KeyError, TypeError, ValueError) as e:
        return _WriteErrorMessage(str(e), 400)
      except ForbiddenError as e:
        return _WriteErrorMessage(str(e), 403)

      response = make_response(json.dumps(results))
      _SetCorsHeadersIfAppropriate(request, response)
      return response

    Wrapper.__name__ = request_handler.__name__
    return Wrapper

  return RequestHandlerDecorator


def _SetCorsHeadersIfAppropriate(cur_request, response):
  response.headers['Content-Type'] = 'application/json; charset=utf-8'
  set_cors_headers = False
  origin = cur_request.headers.get('Origin', '')
  for allowed in _ALLOWED_ORIGINS:
    dev_pattern = re.compile(r'https://[A-Za-z0-9-]+-dot-' + re.escape(allowed))
    prod_pattern = re.compile(r'https://' + re.escape(allowed))
    if dev_pattern.match(origin) or prod_pattern.match(origin):
      set_cors_headers = True
  if set_cors_headers:
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET,OPTIONS,POST'
    response.headers[
        'Access-Control-Allow-Headers'] = 'Accept,Authorization,Content-Type'
    response.headers['Access-Control-Max-Age'] = '3600'


def _WriteErrorMessage(message, status):
  logging.error(traceback.format_exc())
  return make_response(json.dumps({'error': message}), status)
