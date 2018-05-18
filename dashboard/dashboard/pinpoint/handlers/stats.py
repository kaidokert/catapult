# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provides the web interface for displaying an overview of jobs."""

import json
import logging
import webapp2

from dashboard.pinpoint.models import job as job_module


_MAX_JOBS_TO_FETCH = 500


# TODO: Generalize the Jobs handler to allow the user to choose what fields to
# include and how many Jobs to fertch.

class Stats(webapp2.RequestHandler):
  """Shows an overview of recent anomalies for perf sheriffing."""

  def get(self):
    self.response.out.write(json.dumps(_GetJobs()))


def _GetJobs():
  query = job_module.Job.query().order(-job_module.Job.created)

  job_infos = []

  start_cursor = None
  jobs = query.fetch(
      _MAX_JOBS_TO_FETCH, 
      keys_only=False, use_cache=False)

  for job in jobs:
    #job = k.get(use_cache=False)
    logging.info('JobId: %s' % job.job_id)
    if not job.auto_explore:
      continue
    diffs = 0
    status = job.status
    attempts = 0
    for c in job.state._changes:
      attempts += len(job.state._attempts[c])
    if attempts > 1000:
      diffs = 0
      status = 'Failed'
    else:
      diffs = len(list(job.state.Differences()))

    job_infos.append({
        'job_id': job.job_id,
        'created': job.created.isoformat(),
        # TODO: Don't access JobState outside of the Job object.
        'differences': diffs,
        'status': status,
        'bug_id': job.bug_id,
        'exception': job.exception,
        'arguments': job.arguments
    })
    logging.info(' -> done')

  return job_infos
