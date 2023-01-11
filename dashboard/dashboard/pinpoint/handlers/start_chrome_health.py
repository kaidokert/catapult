# Copyright 2022 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Chrome Health Initiative (CHI) Job Scheduler


"""

import json
import logging
# import os

# from dashboard.common import datastore_hooks
from dashboard.common import utils
# from dashboard.services import pinpoint_service
from dashboard.services import request

_PINPOINT_URL = 'https://pinpoint-dot-chromeperf.appspot.com'

class InvalidParamsError(Exception):
  pass


logging.debug('chrome health flask app')
def StartChromeHealthHandler():
  logging.debug('chrome health trigger job run handler')
  try:
    pinpoint_params = _StartChromeHealthJobs()
    logging.debug('chrome health parameters generated')
  except InvalidParamsError as e:
    return json.dumps({'error': str(e)})

  # return_args = json.dumps(pinpoint_service.NewJob(pinpoint_params))

  # logging.debug(return_args)

  """Submits a new job request to Pinpoint."""
  return _Request(_PINPOINT_URL + '/api/new', pinpoint_params)


if not utils.IsRunningFlask():
  import webapp2

  class StartChromeHealth(webapp2.RequestHandler):

    def get(self):
      # logging.debug('chrome health os environment info %s', os.environ)
      _StartChromeHealthJobs()


def _StartChromeHealthJobs():
  """Starts Chrome Health jobs

  Use this logging to help parameters: 
  https://pantheon.corp.google.com/logs/query;cursorTimestamp=2022-12-14T01:09:39.910665Z;query=resource.type%3D%22gae_app%22%0Aresource.labels.module_id%3D%22pinpoint%22%0A%22Received%20Params%22%0Atimestamp%3D%222022-12-14T01:09:39.910665Z%22%0AinsertId%3D%221a2mmusffrplwr%22;timeRange=PT15M?project=chromeperf

  Returns:
    A dict of params for passing to Pinpoint to start a job, or a dict with an
    'error' field.
  """
  # if not utils.IsValidSheriffUser():
  #   user = utils.GetEmail()
  #   raise InvalidParamsError('User "%s" not authorized.' % user)

  # logging.debug('chrome health user authorized')

  # email = utils.GetEmail()
  # datastore_hooks.SetPrivilegedRequest(flask_flag=True)

  bot_name = 'mac-m1_mini_2020-perf-pgo'
  benchmark = 'jetstream2'
  job_name = 'Try job on %s/%s' % (bot_name, benchmark)

  # There may be other ways to get the git hash: ResolveToGitHash
  # start_git_hash = ResolveToGitHash(start_commit, suite)

  pinpoint_params = {
      'comparison_mode': 'try',
      'configuration': bot_name,
      'benchmark': benchmark,
      'base_git_hash': '410951fc34bb4b2cbf182231f9f779efaafaf682',
      'end_git_hash': 'a439150e9b637137ead135bf7ff92d615ad5be9a',
      'extra_test_args': '',
      'initial_attempt_count': '8',
      'project': 'chromium',
      'story': 'JetStream2',
      'target': 'performance_test_suite',
      'try': 'on',
      # 'user': 'sunxiaodi@google.com',
      'name': job_name,
      'story_tags': '',
      'chart': '',
      'statistic': '',
      'comparison_magnitude': '',
      'extra_test_args': '',
      'base_patch': '',
      'experiment_patch': '',
      'base_extra_args': '',
      'experiment_extra_args': '',
      'bug_id': '',
      'batch_id': ''
  }

  return pinpoint_params


def _Request(endpoint, params):
  """Sends a request to an endpoint and returns JSON data."""
  # assert datastore_hooks.IsUnalteredQueryPermitted()
  logging.error('chrome health trigger _request')
  try:
    return request.RequestJson(
        endpoint, method='POST', use_cache=False, use_auth=True, **params)
  except request.RequestError as e:
    try:
      return json.loads(e.content)
    except ValueError:
      # for errors.SwarmingNoBots()
      return {"error":str(e)}
