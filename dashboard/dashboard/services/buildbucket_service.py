# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Encapsulates a simplistic interface to the buildbucket service."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json

from dashboard.services import request

API_BASE_URL = 'https://cr-buildbucket.appspot.com/api/buildbucket/v1/'


def LegacyPut(bucket, tags, parameters, pubsub_callback=None):
  """Creates a new build via buildbucket's legacy API.

  Args:
    * bucket - the legacy name of the bucket to schedule in
      (e.g. luci.project_name.bucket_name).
    * tags - a list of strings to tag the build with.
    * parameters - a JSON object with no well-defined form.
    * pubsub_callback - a JSON object with no well-defined form.

  Returns a bespoke JSON object with no well-defined form.
  """
  body = {
      'bucket': bucket,
      'tags': tags,
      'parameters_json': json.dumps(parameters, separators=(',', ':')),
  }
  if pubsub_callback:
    body['pubsub_callback'] = pubsub_callback
  return request.RequestJson(API_BASE_URL + 'builds', method='PUT', body=body)


def LegacyGetJobStatus(job_id):
  """Gets the details of a job via buildbucket's legacy API.

  Returns a bespoke JSON object with no well-defined form.
  """
  return request.RequestJson(API_BASE_URL + 'builds/%s' % (job_id))


# TODO(robertocn): Implement CancelJobByID
