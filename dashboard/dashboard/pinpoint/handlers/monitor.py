# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provides the web interface for displaying an overview of jobs."""

import datetime
import logging
import webapp2

from dashboard.pinpoint.models import job as job_module


class Monitor(webapp2.RequestHandler):
  """Looks for jobs with old tasks and re-kicks them."""

  def get(self):
    jobs = job_module.Job.query(job_module.Job.task != None).fetch()
    for job in jobs:
      if datetime.datetime.now() - job.updated < datetime.timedelta(minutes=10):
        # Still fresh! Do nothing.
        continue

      # Stale. Re-kick the job.
      logging.warning(job.job_id)
      job.Schedule()
      job.put()
