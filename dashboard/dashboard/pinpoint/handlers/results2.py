# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provides the web interface for displaying a results2 file."""

import collections
import os
import StringIO
import threading
import webapp2

from dashboard.pinpoint.models import job as job_module
from dashboard.pinpoint.models.quest import read_value
from tracing_build import render_histograms_viewer


from tracing.value import histogram as histogram_module
from tracing.value import histogram_set
from tracing.value.diagnostics import reserved_infos


class Results2Error(Exception):

  pass


class Results2(webapp2.RequestHandler):
  """Shows an overview of recent anomalies for perf sheriffing."""

  def get(self, job_id):
    try:
      job_data = _GetJobData(job_id)

      histogram_data_by_commit = _FetchHistogramsDataFromJobData(job_data)

      histogram_dicts = []
      for commit_name, histograms in histogram_data_by_commit.iteritems():
        hs = histogram_set.HistogramSet()
        for h in histograms:
          hs.ImportDicts(h)
        hs.AddSharedDiagnostic(
            reserved_infos.LABELS.name,
            histogram_module.GenericSet([commit_name]))
        histogram_dicts.extend(hs.AsDicts())
        histogram_data_by_commit[commit_name] = None

      vulcanized_html = _ReadVulcanizedHistogramsViewer()
      vulcanized_html_and_histograms = StringIO.StringIO()
      render_histograms_viewer.RenderHistogramsViewer(
          histogram_dicts, vulcanized_html_and_histograms,
          vulcanized_html=vulcanized_html)
      self.response.out.write(vulcanized_html_and_histograms.getvalue())
    except Results2Error as e:
      self.response.set_status(400)
      self.response.out.write(e.message)
      return


def _GetChangeName(change_dict):
  names = []
  for d in change_dict:
    names.append('%s@%s' % (d['repository'], d['git_hash'][:7]))
  return ' '.join(names)


def _ReadVulcanizedHistogramsViewer():
  viewer_path = os.path.join(
      os.path.dirname(__file__), '..', '..', '..',
      'vulcanized_histograms_viewer', 'vulcanized_histograms_viewer.html')
  with open(viewer_path, 'r') as f:
    return f.read()


def _FetchHistogramsDataFromJobData(job_data):
  histogram_data_by_commit = collections.defaultdict(list)
  threads = []
  lock = threading.Lock()

  test_index = -1
  for i in xrange(len(job_data['quests'])):
    if job_data['quests'][i] == 'Test':
      test_index = i
      break

  if test_index == -1:
    raise Results2Error('No Test quest.')

  attempts = job_data['attempts']
  changes = job_data['changes']

  for i in xrange(len(attempts)):
    name = _GetChangeName(changes[i]['commits'])

    for j in xrange(len(attempts[i])):
      executions = attempts[i][j].get('executions')
      if not executions:
        continue
      result_arguments = executions[test_index].get('result_arguments', {})
      isolate_hash = result_arguments.get('isolate_hash')
      if not isolate_hash:
        continue

      t = threading.Thread(
          target=_FetchHistogramFromIsolate,
          args=(name, isolate_hash, histogram_data_by_commit, lock))
      threads.append(t)

  # We use threading since httplib2 provides no async functions.
  for t in threads:
    t.start()
  for t in threads:
    t.join()

  return histogram_data_by_commit


def _GetJobData(job_id):
  job = job_module.JobFromId(job_id)
  if not job:
    raise Results2Error('Error: Job %s missing' % job_id)

  job_data = job.AsDict()
  return job_data


def _FetchHistogramFromIsolate(commit_name, isolate_hash, results, lock):
  histogram_output = read_value._RetrieveOutputJson(
      isolate_hash, 'chartjson-output.json')
  if not histogram_output:
    return
  with lock:
    results[commit_name].append(histogram_output)
