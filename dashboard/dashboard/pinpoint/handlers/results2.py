# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provides the web interface for displaying a results2 file."""

import cloudstorage
import json
import os
import webapp2

from dashboard.pinpoint.models import job as job_module
from dashboard.pinpoint.models.quest import read_value
from tracing_build import render_histograms_viewer


class Results2Error(Exception):

  pass


# pylint: disable=invalid-name

class _GcsFileStream(object):
  def __init__(self, filename, params):
    self.gcs_file = cloudstorage.open(
        filename, 'w', content_type='text/html', retry_params=params)

  def seek(self, _):
    pass

  def truncate(self):
    pass

  def write(self, data):
    self.gcs_file.write(data)

  def close(self):
    self.gcs_file.close()

# pylint: enable=invalid-name


class Results2(webapp2.RequestHandler):
  """Shows an overview of recent anomalies for perf sheriffing."""

  def get(self, job_id):
    try:
      filename = '/chromeperf.appspot.com/results2/%s.html' % job_id
      results = cloudstorage.listbucket(filename)

      for _ in results:
        self.response.out.write(json.dumps(
            {
                'status': 'complete',
                'url': 'https://storage.cloud.google.com' + filename
            }))
        return

      job = job_module.JobFromId(job_id)
      if not job:
        raise Results2Error('Error: Job %s missing' % job_id)

      self.response.out.write(json.dumps(
          {'status': job.ScheduleResults2Generation()}))

    except Results2Error as e:
      self.response.set_status(400)
      self.response.out.write(e.message)
      return

  def post(self, job_id):
    try:
      histogram_dicts = _FetchHistogramsDataFromJobData(job_id)
      vulcanized_html = _ReadVulcanizedHistogramsViewer()

      job_module.JobCachedResults2(job_id=job_id).put()

      filename = '/chromeperf.appspot.com/results2/%s.html' % job_id
      gcs_file = _GcsFileStream(
          filename, cloudstorage.RetryParams(backoff_factor=1.1))

      render_histograms_viewer.RenderHistogramsViewer(
          histogram_dicts, gcs_file,
          reset_results=True, vulcanized_html=vulcanized_html)

      gcs_file.close()
    except Results2Error as e:
      self.response.out.write(e.message)


def _GetJobData(job_id):
  job = job_module.JobFromId(job_id)
  if not job:
    raise Results2Error('Error: Job %s missing' % job_id)

  return job.AsDict(options=(job_module.OPTION_STATE,))


def _ReadVulcanizedHistogramsViewer():
  viewer_path = os.path.join(
      os.path.dirname(__file__), '..', '..', '..',
      'vulcanized_histograms_viewer', 'vulcanized_histograms_viewer.html')
  with open(viewer_path, 'r') as f:
    return f.read()


class  _FetchHistogramsDataFromJobData(object):
  def __init__(self, job_id):
    self.isolate_hashes = self._GetAllIsolateHashesForJob(job_id)

  def _GetAllIsolateHashesForJob(self, job_id):
    job_data = _GetJobData(job_id)

    quest_index = None
    for quest_index in xrange(len(job_data['quests'])):
      if job_data['quests'][quest_index] == 'Test':
        break
    else:
      raise Results2Error('No Test quest.')

    isolate_hashes = []

    # If there are differences, only include Changes with differences.
    for change_index in xrange(len(job_data['changes'])):
      if not _IsChangeDifferent(job_data, change_index):
        continue
      isolate_hashes += _GetIsolateHashesForChange(
          job_data, change_index, quest_index)

    # Otherwise, just include all Changes.
    if not isolate_hashes:
      for change_index in xrange(len(job_data['changes'])):
        isolate_hashes += _GetIsolateHashesForChange(
            job_data, change_index, quest_index)

    return isolate_hashes

  def __iter__(self):
    for isolate_hash in self.isolate_hashes:
      hs = _FetchHistogramFromIsolate(isolate_hash)
      for h in hs:
        yield h
      del hs


def _IsChangeDifferent(job_data, change_index):
  if (change_index > 0 and
      job_data['comparisons'][change_index - 1] == 'different'):
    return True

  if (change_index < len(job_data['changes']) - 1 and
      job_data['comparisons'][change_index] == 'different'):
    return True

  return False


def _GetIsolateHashesForChange(job_data, change_index, quest_index):
  isolate_hashes = []
  attempts = job_data['attempts'][change_index]
  for attempt_info in attempts:
    executions = attempt_info['executions']
    if quest_index >= len(executions):
      continue

    result_arguments = executions[quest_index]['result_arguments']
    if 'isolate_hash' not in result_arguments:
      continue

    isolate_hashes.append(result_arguments['isolate_hash'])

  return isolate_hashes


def _FetchHistogramFromIsolate(isolate_hash):
  return read_value._RetrieveOutputJson(
      isolate_hash, 'chartjson-output.json')
