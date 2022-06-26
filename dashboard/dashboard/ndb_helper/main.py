# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Dispatches requests to request handler classes."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import logging
import google.cloud.logging
google.cloud.logging.Client().setup_logging(log_level=logging.DEBUG)

from dashboard.pinpoint.models import job as job_module

from flask import Flask

APP = Flask(__name__)

from google.appengine.api import wrap_wsgi_app
APP.wsgi_app = wrap_wsgi_app(APP.wsgi_app)

from flask import make_response, request


@APP.route('/api/job/<job_id>')
def JobHandlerGet(job_id):
  try:
    job = job_module.JobFromId(job_id)
  except ValueError:
    return make_response(
        json.dumps({'ndb-helper error': 'Invalid job id: %s' % job_id}), 400)

  if not job:
    return make_response(
        json.dumps({'ndb-helper error': 'Unknown job id: %s' % job_id}), 404)

  opts = request.args.getlist('o')
  return make_response(json.dumps(job.AsDict(opts)))
