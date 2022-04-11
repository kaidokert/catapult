# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Encapsulates a simplistic interface to the buildbucket service."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import logging
import json
import re
import uuid

from dashboard.services import request
from dashboard.common import utils

API_BASE_URL = 'https://cr-buildbucket.appspot.com/api/buildbucket/v1/'
API_BASE_URL2 = 'https://cr-buildbucket.appspot.com/prpc/buildbucket.v2.Builds/'

# Default Buildbucket bucket name.
_BUCKET_NAME = 'master.tryserver.chromium.perf'

# Gitiles commit buildset pattern. Example:
# ('commit/gitiles/chromium.googlesource.com/infra/luci/luci-go/+/'
#  'b7a757f457487cd5cfe2dae83f65c5bc10e288b7')
RE_BUILDSET_GITILES_COMMIT = re.compile(
    r'^commit/gitiles/([^/]+)/(.+?)/\+/([a-f0-9]{40})$')
# Gerrit CL buildset pattern. Example:
# patch/gerrit/chromium-review.googlesource.com/677784/5
RE_BUILDSET_GERRIT_CL = re.compile(r'^patch/gerrit/([^/]+)/(\d+)/(\d+)$')

_BUCKET_RE = re.compile(r'luci\.([^.]+)\.([^.]+)')

def Put(bucket, tags, parameters):
  if utils.IsRunningBuildBucketV2():
    return PutV2(bucket, tags, parameters)
  return PutV1(bucket, tags, parameters)


def PutV1(bucket, tags, parameters, pubsub_callback=None):
  body = {
      'bucket': bucket,
      'tags': tags,
      'parameters_json': json.dumps(parameters, separators=(',', ':')),
  }
  if pubsub_callback:
    body['pubsub_callback'] = pubsub_callback
  return request.RequestJson(API_BASE_URL + 'builds', method='PUT', body=body)


def PutV2(bucket, tags, parameters):
  bucket_parts = _BUCKET_RE.split(bucket)
  if len(bucket_parts) != 4:
    raise ValueError('Could not parse bucket value: %s' % bucket)
  project = bucket_parts[1]
  bucket = bucket_parts[2]
  tags_kvp, gerrit_changes, gitiles_commit = [], [], []
  for k, v in [tag.split(':') for tag in tags]:
    tags_kvp.append({'key': k, 'value': v})
    if k == 'buildset':
      match = RE_BUILDSET_GERRIT_CL.match(v)
      if match:
        gerrit_changes.append({
            "host": match.group(1),
            "change": match.group(2),
            "patchset": match.group(3)
        })
      match = RE_BUILDSET_GITILES_COMMIT.match(v)
      if match:
        gitiles_commit.append({
            "host": match.group(1),
            "project": match.group(2),
            "id": match.group(3)
        })
  body = {
      'requestId': str(uuid.uuid4()),
      'builder': {
          'project': project,
          'bucket': bucket,
          'builder': parameters['builder_name'],
      },
      # Make sure 'tags' gets formatted like StringPair expects:
      # [{'key': key, 'value'; value}]
      'tags': tags_kvp,
      'properties': parameters.get('properties', {}),
  }
  if gerrit_changes:
    body['gerritChanges'] = gerrit_changes
  if gitiles_commit:
    body['gitilesCommit'] = gitiles_commit
  logging.info("bbv2 Put body: \n%s\n", json.dumps(body))

  return request.RequestJson(
      API_BASE_URL2 + 'ScheduleBuild', method='POST', body=body)


def GetJobStatus(job_id):
  if utils.IsRunningBuildBucketV2():
    return GetJobStatusV2(job_id)
  return GetJobStatusV1(job_id)


def GetJobStatusV1(job_id):
  """Gets the details of a job via buildbucket's API."""
  return request.RequestJson(API_BASE_URL + 'builds/%s' % (job_id))


# TODO: Rename to Get().
def GetJobStatusV2(job_id):
  """Gets the details of a job via buildbucket's API."""
  body = json.dumps({
      'id': job_id
  })
  return request.RequestJson(
      API_BASE_URL2 + 'GetBuild', method='POST', body=body)


# TODO(robertocn): Implement CancelJobByID
