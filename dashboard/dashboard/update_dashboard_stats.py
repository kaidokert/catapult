# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import time

from google.appengine.ext import deferred

from dashboard import add_histograms
from dashboard.common import request_handler
from dashboard.pinpoint.models import job as job_module
from dashboard.pinpoint.models import job_state

from tracing.value import histogram as histogram_module
from tracing.value import histogram_set
from tracing.value.diagnostics import generic_set
from tracing.value.diagnostics import reserved_infos

_MAX_JOBS_TO_FETCH = 100


class UpdateDashboardStatsHandler(request_handler.RequestHandler):
  """A simple request handler to refresh the cached test suites info."""

  def get(self):
    self.post()

  def post(self):
    _FetchDashboardStats()


def _FetchCompletedPinpointJobs(start_date):
  query = job_module.Job.query().order(-job_module.Job.created)
  jobs, next_cursor, more = query.fetch_page(_MAX_JOBS_TO_FETCH)

  def _IsValidJob(job):
    if job.status != 'Completed':
      return False
    if not job.bug_id:
      return False
    if not hasattr(job.state, '_comparison_mode'):
      return False
    if job.state.comparison_mode != job_state.PERFORMANCE:
      return False
    diffs = len(list(job.state.Differences()))
    if diffs != 1:
      return False
    return True

  jobs_in_range = [j for j in jobs if j.created > start_date]
  valid_jobs = [j for j in jobs_in_range if _IsValidJob(j)]
  total_jobs = []
  total_jobs.extend(valid_jobs)

  while jobs_in_range and more:
    jobs, next_cursor, more = query.fetch_page(
        _MAX_JOBS_TO_FETCH, start_cursor=next_cursor)
    jobs_in_range = [j for j in jobs if j.created > start_date]
    valid_jobs = [j for j in jobs_in_range if _IsValidJob(j)]
    total_jobs.extend(valid_jobs)

  return total_jobs


def _CreateHistogramSet(
    master, bot, benchmark, commit_position,
    commit_to_culprit, job_to_culprit):
  histograms = histogram_set.HistogramSet([commit_to_culprit, job_to_culprit])
  histograms.AddSharedDiagnostic(
      reserved_infos.MASTERS.name,
      generic_set.GenericSet([master]))
  histograms.AddSharedDiagnostic(
      reserved_infos.BOTS.name,
      generic_set.GenericSet([bot]))
  histograms.AddSharedDiagnostic(
      reserved_infos.CHROMIUM_COMMIT_POSITIONS.name,
      generic_set.GenericSet([commit_position]))
  histograms.AddSharedDiagnostic(
      reserved_infos.BENCHMARKS.name,
      generic_set.GenericSet([benchmark]))

  return histograms


def _FetchDashboardStats():
  completed_jobs = _FetchCompletedPinpointJobs(
      datetime.datetime.now() - datetime.timedelta(days=14))

  commit_to_culprit = histogram_module.Histogram('commitToCulprit', 'ms')
  job_to_culprit = histogram_module.Histogram('jobToCulprit', 'ms')

  if not completed_jobs:
    return

  for j in completed_jobs:
    diffs = j.state.Differences()
    for d in diffs:
      diff = d[1].AsDict()
      break

    land_time = datetime.datetime.strptime(
        diff['commits'][0]['time'], '%c')
    culprit_time = j.updated
    create_time = j.created

    time_diff = culprit_time - land_time

    time_from_job_to_culprit = (
        culprit_time - create_time).total_seconds() * 1000.0
    time_from_land_to_culprit = time_diff.total_seconds() * 1000.0
    commit_to_culprit.AddSample(time_from_land_to_culprit)
    job_to_culprit.AddSample(time_from_job_to_culprit)

  hs = _CreateHistogramSet(
      'ChromiumPerfFyi', 'test1', 'chromeperf.stats',
      int(time.time()), commit_to_culprit, job_to_culprit)

  deferred.defer(
      add_histograms.ProcessHistogramSet, hs.AsDicts())

