import json
import datetime
from dashboard.api import utils
from dashboard.common import layered_cache
from dashboard.pinpoint.models import job
from dashboard.pinpoint.models import job_state
from dashboard.services import buildbucket_service
from dashboard.services import swarming


def jobTotalTime(j):
  return j.updated - j.created

def jobTotalBuildTime(j):
  times = []

  for k, a in j.state._attempts.iteritems():
    a = [att for att in a][0]
    e = a._executions[0]
    if e._build:
      build = buildbucket_service.GetJobStatus(e._build)['build']

      ts1 = build['created_ts']
      ts2 = build['updated_ts']

      d1 = datetime.datetime.fromtimestamp(float(ts1) / 1000000.0)
      d2 = datetime.datetime.fromtimestamp(float(ts2) / 1000000.0)

      times.append(d2 - d1)
  return sum(times, datetime.timedelta(minutes=0))

def jobTotalTaskTime(j):
  times = []
  i = 0
  for k, atts in j.state._attempts.iteritems():
    for a in atts:
      i += 1
      k = 'pinpoint_job_stats_atts_2019-05-07-%s[%s]' % (j.job_id, i)
      v = layered_cache.Get(k)
      if v:
        times.append(v)
        continue

      if len(a._executions) < 2:
        continue
      e = a._executions[1]
      s = swarming.Swarming(e._swarming_server).Task(e._task_id)
      r = s.Result()
      d1 = utils.ParseISO8601(r['started_ts'])
      d2 = utils.ParseISO8601(r['completed_ts'])
      times.append(d2 - d1)

      v = times[-1]
      layered_cache.Set(k, v, days_to_keep=30)

  return sum(times, datetime.timedelta(minutes=0))

def _CheckJob(job_id):
  j = job.JobFromId(job_id)
  k = 'pinpoint_job_stats_2019-05-07-%s' % j.job_id
  v = layered_cache.Get(k)
  if not v:
    v = (jobTotalTime(j), jobTotalTaskTime(j))
    layered_cache.Set(k, v, days_to_keep=30)
    print 'SET'
  print v

def _FetchCompletedPinpointJobs():
  query = job.Job.query().order(-job.Job.created)
  jobs, next_cursor, more = query.fetch_page(150)

  def _IsValidJob(j):
    if j.status != 'Completed':
      return False
    if not j.bug_id:
      return False
    if j.comparison_mode != job_state.PERFORMANCE:
      return False
    return True

  valid_jobs = [j for j in jobs if _IsValidJob(j)]

  for j in valid_jobs:
    _CheckJob(j.job_id)
