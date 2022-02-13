# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Encapsulates a simplistic interface to the buildbucket service."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json

from dashboard.services import request

#API_BASE_URL = 'https://cr-buildbucket.apapspot.com/api/buildbucket/v1/'

API_BASE_URL = 'https://cr-buildbucket.appspot.com/prpc/buildbucket.v2.Builds/'

# Default Buildbucket bucket name.
_BUCKET_NAME = 'master.tryserver.chromium.perf'


def Put(bucket, tags, parameters, pubsub_callback=None):
  body = {
      'builder': {
          'project': '',
          'bucket': bucket,
          'builder': ''
      },
      'tags': tags,
      # parameters_json does not appear to exist in the new api.
      # TODO: Delete this and see if anyone notices.
      'parameters_json': json.dumps(parameters, separators=(',', ':')),
  }
  if pubsub_callback:
    body['pubsub_callback'] = pubsub_callback
  return request.RequestJson(API_BASE_URL + 'ScheduleBuild', method='POST',
                             body=body)


# TODO: Rename to Get().
def GetJobStatus(job_id):
  """Gets the details of a job via buildbucket's API."""
  body = json.dumps({
      'id': job_id
  })
  return request.RequestJson(API_BASE_URL + 'GetBuild', method='POST',
                             body=body)


# TODO(robertocn): Implement CancelJobByID
