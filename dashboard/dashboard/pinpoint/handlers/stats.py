# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provides the web interface for displaying an overview of jobs."""

import json
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
  for _ in xrange(10):
    jobs, start_cursor, more = query.fetch_page(
        _MAX_JOBS_TO_FETCH / 10, start_cursor=start_cursor)

    for job in jobs:
      if not job.auto_explore:
        continue
      job_infos.append({
          'job_id': job.job_id,
          'created': job.created.isoformat(),
          # TODO: Don't access JobState outside of the Job object.
          'differences': len(list(job.state.Differences())),
          'status': job.status,
          'bug_id': job.bug_id,
          'exception': job.exception,
          'arguments': job.arguments
      })
    jobs = None
    if not more:
      break

  return job_infos
