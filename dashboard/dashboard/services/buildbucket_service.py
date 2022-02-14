# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Encapsulates a simplistic interface to the buildbucket service."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json

from dashboard.services import request

API_BASE_URL = 'https://cr-buildbucket.appspot.com/prpc/buildbucket.v2.Builds/'

# Default Buildbucket bucket name.
_BUCKET_NAME = 'master.tryserver.chromium.perf'


def Put(bucket, tags, parameters, pubsub_callback=None):
  body = {
      'builder': {
          'project': '', # TODO: figure out what goes here.
          'bucket': bucket,
          'builder': '' # TODO: figure out what goes here.
      },
      # Make sure 'tags' gets formatted like StringPair expects:
      # [{'key': key, 'value'; value}]
      'tags':  [{'key': v[0], 'value': v[1]} for v in [
          e.split(':') for e in tags]],
      'properties': json.dumps(parameters, separators=(',', ':')),
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
