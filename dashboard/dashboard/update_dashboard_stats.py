# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import time

from google.appengine.ext import deferred
from google.appengine.ext import ndb

from dashboard import add_histograms
from dashboard.common import request_handler
from dashboard.models import anomaly
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


def _GetDiffCommitTimeFromJob(job):
  diffs = job.state.Differences()
  for d in diffs:
    diff = d[1].AsDict()
    commit_time = datetime.datetime.strptime(
        diff['commits'][0]['time'], '%a %b %d %X %Y')
    return commit_time
  return None


@ndb.tasklet
def _FetchStatsForJob(job):
  commit_time = _GetDiffCommitTimeFromJob(job)
  if not commit_time:
    raise ndb.Return(None)

  culprit_time = job.updated
  create_time = job.created

  # Alert time, we'll approximate this out by querying for all alerts for this
  # bug and taking the earliest.
  alerts, _, _ = yield anomaly.Anomaly.QueryAsync(
      bug_id=job.bug_id, limit=1000)
  if not alerts:
    raise ndb.Return(None)

  alert_time = min([a.timestamp for a in alerts])
  if alert_time < commit_time:
    raise ndb.Return(None)

  time_from_job_to_culprit = (
      culprit_time - create_time).total_seconds() * 1000.0
  time_from_commit_to_alert = (
      alert_time - commit_time).total_seconds() * 1000.0
  time_from_alert_to_job = (
      create_time - alert_time).total_seconds() * 1000.0
  time_from_commit_to_culprit = (
      culprit_time - commit_time).total_seconds() * 1000.0

  raise ndb.Return((
      time_from_commit_to_culprit,
      time_from_commit_to_alert,
      time_from_alert_to_job,
      time_from_job_to_culprit))


@ndb.synctasklet
def _FetchDashboardStats():
  completed_jobs = _FetchCompletedPinpointJobs(
      datetime.datetime.now() - datetime.timedelta(days=14))

  job_results = yield [_FetchStatsForJob(j) for j in completed_jobs]
  job_results = [j for j in job_results if j]
  if not job_results:
    return

  commit_to_culprit = histogram_module.Histogram('pinpoint', 'ms')
  commit_to_alert = histogram_module.Histogram('pinpoint', 'ms')
  commit_to_alert.diagnostics[reserved_infos.STORIES.name] = (
      generic_set.GenericSet(['commitToAlert']))
  alert_to_job = histogram_module.Histogram('pinpoint', 'ms')
  alert_to_job.diagnostics[reserved_infos.STORIES.name] = (
      generic_set.GenericSet(['alertToJob']))
  job_to_culprit = histogram_module.Histogram('pinpoint', 'ms')
  job_to_culprit.diagnostics[reserved_infos.STORIES.name] = (
      generic_set.GenericSet(['jobToCulprit']))

  for result in job_results:
    time_from_land_to_culprit = result[0]
    time_from_commit_to_alert = result[1]
    time_from_alert_to_job = result[2]
    time_from_job_to_culprit = result[3]

    commit_to_alert.AddSample(time_from_commit_to_alert)
    alert_to_job.AddSample(time_from_alert_to_job)
    job_to_culprit.AddSample(time_from_job_to_culprit)
    commit_to_culprit.AddSample(time_from_land_to_culprit)

  hs = _CreateHistogramSet(
      'ChromiumPerfFyi', 'test1', 'chromeperf.stats',
      int(time.time()), commit_to_culprit, job_to_culprit)

  deferred.defer(
      add_histograms.ProcessHistogramSet, hs.AsDicts())

