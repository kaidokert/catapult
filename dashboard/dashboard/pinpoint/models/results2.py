# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import cloudstorage
import logging
import os

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from dashboard.pinpoint.models import job_state
from dashboard.pinpoint.models.quest import read_value
from dashboard.pinpoint.models.quest import run_test
from dashboard.services import swarming
from tracing_build import render_histograms_viewer
from tracing.value import gtest_json_converter
from tracing.value.diagnostics import generic_set
from tracing.value.diagnostics import reserved_infos

# from util import big_query_utils

class Results2Error(Exception):

  pass


class CachedResults2(ndb.Model):
  """Stores data on when a results2 was generated."""

  updated = ndb.DateTimeProperty(required=True, auto_now_add=True)
  job_id = ndb.StringProperty()


class _GcsFileStream(object):
  """Wraps a gcs file providing a FileStream like api."""

  # pylint: disable=invalid-name

  def __init__(self, *args, **kwargs):
    self._gcs_file = cloudstorage.open(*args, **kwargs)

  def seek(self, _):
    pass

  def truncate(self):
    pass

  def write(self, data):
    self._gcs_file.write(data)

  def close(self):
    self._gcs_file.close()


def _GetCloudStorageName(job_id):
  return '/results2-public/%s.html' % job_id


def GetCachedResults2(job):
  filename = _GetCloudStorageName(job.job_id)
  results = cloudstorage.listbucket(filename)

  for _ in results:
    return 'https://storage.cloud.google.com' + filename

  return None


def ScheduleResults2Generation(job):
  logging.debug('Job [%s]: ScheduleResults2Generation', job.job_id)
  try:
    # Don't want several tasks creating results2, so create task with specific
    # name to deduplicate.
    task_name = 'results2-public-%s' % job.job_id
    taskqueue.add(
        queue_name='job-queue',
        url='/api/generate-results2/' + job.job_id,
        name=task_name)
  except taskqueue.TombstonedTaskError:
    return False
  except taskqueue.TaskAlreadyExistsError:
    pass
  return True


def GenerateResults2(job):
  logging.debug('Job [%s]: GenerateResults2', job.job_id)

  vulcanized_html = _ReadVulcanizedHistogramsViewer()

  CachedResults2(job_id=job.job_id).put()

  filename = _GetCloudStorageName(job.job_id)
  gcs_file = _GcsFileStream(
      filename,
      'w',
      content_type='text/html',
      retry_params=cloudstorage.RetryParams(backoff_factor=1.1))

  render_histograms_viewer.RenderHistogramsViewer(
      _FetchHistograms(job),
      gcs_file,
      reset_results=True,
      vulcanized_html=vulcanized_html)

  gcs_file.close()
  logging.debug('Generated %s; see https://storage.cloud.google.com%s',
                filename, filename)

  # Only save A/B tests to BQ
  if job.comparison_mode != job_state.FUNCTIONAL and job.comparison_mode != job_state.PERFORMANCE:
    try:
      _SaveJobToBigQuery(job)
    except Exception as e:
      logging.error(e)
  else:
    logging.error("NO BQ?!?!?!!?")


def _ReadVulcanizedHistogramsViewer():
  viewer_path = os.path.join(
      os.path.dirname(__file__), '..', '..', '..',
      'vulcanized_histograms_viewer', 'vulcanized_histograms_viewer.html')
  with open(viewer_path, 'r') as f:
    return f.read()



HistogramMetadata = collections.namedtuple('HistogramMetadata',
  ['attemptNo', "change", "swarming_result"])

def _FetchHistograms(job):
  for change in _ChangeList(job):
    for attemptNo, attempt in enumerate(job.state._attempts[change]):
      swarming_result = None
      for execution in attempt.executions:
        # Attempt to extract taskID if this is a run_test._RunTestExecution
        if isinstance(execution, run_test._RunTestExecution):
          # Query Swarming
          try:
            swarming_task = swarming.Swarming(execution._swarming_server).Task(execution._task_id)
            logging.error("SWARMINGTASKWORKEDWOO: " + str(swarming_task))
            swarming_result = swarming_task.Result()
            logging.error("SWARMRESULT: " + str(swarming_result))
          except Exception as e:
            logging.error("_FetchHistograms _RunTestExecutions error: " + str(e))
          continue

        # Attempt to extract Histograms if this is a read_value.*
        mode = None
        if isinstance(execution, read_value._ReadHistogramsJsonValueExecution):
          mode = 'histograms'
        elif isinstance(execution, read_value._ReadGraphJsonValueExecution):
          mode = 'graphjson'
        elif isinstance(execution, read_value.ReadValueExecution):
          mode = execution.mode or 'histograms'

        if mode is None:
          continue

        histogram_sets = None
        if mode == 'graphjson':
          histograms = gtest_json_converter.ConvertGtestJson(
              _JsonFromExecution(execution))
          histograms.AddSharedDiagnosticToAllHistograms(
              reserved_infos.LABELS.name, generic_set.GenericSet([str(change)]))
          histogram_sets = histograms.AsDicts()
        else:
          histogram_sets = _JsonFromExecution(execution)

        logging.debug('Found %s histograms for %s', len(histogram_sets), change)

        metadata = HistogramMetadata(attemptNo, change, swarming_result)
        for histogram in histogram_sets:
          yield render_histograms_viewer.HistogramData(metadata, histogram)

        # Force deletion of histogram_set objects which can be O(100MB).
        del histogram_sets


def _ChangeList(job):
  # If there are differences, only include Changes with differences.
  changes = set()

  for change_a, change_b in job.state.Differences():
    changes.add(change_a)
    changes.add(change_b)

  if changes:
    return list(changes)

  return job.state._changes


def _JsonFromExecution(execution):
  if hasattr(execution, '_cas_root_ref') and execution._cas_root_ref:
    return read_value.RetrieveOutputJsonFromCAS(
        execution._cas_root_ref,
        execution._results_path,
    )

  if hasattr(execution, '_results_filename'):
    results_filename = execution._results_filename
  else:
    results_filename = 'chartjson-output.json'

  if hasattr(execution, '_isolate_server'):
    isolate_server = execution._isolate_server
  else:
    isolate_server = 'https://isolateserver.appspot.com'
  isolate_hash = execution._isolate_hash
  return read_value.RetrieveOutputJson(
      isolate_server,
      isolate_hash,
      results_filename,
  )

_PROJECT_ID = 'todo'
_DATASET = 'todo'
_TABLE = 'todo' # We'll probably have more than one of these
def _SaveJobToBigQuery(job):
  bq = big_query_utils.create_big_query()
  rows = []
  for h in _FetchHistograms(job):
    if "sampleValues" not in h:
      continue
    if len(h["sampleValues"]) != 1:
      # We don't support analysis of metrics with more than one sample.
      continue

    data = {}
    data["batchID"] = job.batch_id
    data["benchmark"] = job.benchmark_arguments.benchmark
    data["cfg"] = job.configuration
    data["change_repo"] = h.metadata.change.repository
    data["change_hash"] = h.metadata.change.git_hash
    data["patch_server"] = None
    data["patch_repo"] = None
    data["patch_number"] = None
    data["patch_rev"] = None
    if h.metadata.change.patch is not None:
      patch_params = h.metadata.change.patch.BuildParameters()
      data["patch_server"] = patch_params["patch_gerrit_url"]
      data["patch_repo"] = patch_params["project"]
      data["patch_number"] = patch_params["patch_issue"]
      data["patch_rev"] = patch_params["patch_rev"]

    if h.metadata.swarming_result and "bot_dimensions" in h.metadata.swarming_result:
      if "device_type" in h.metadata.swarming_result["bot_dimensions"]:
        data["deviceModel"] = h.metadata.swarming_result["bot_dimensions"]["device_type"]
      if "device_os" in h.metadata.swarming_result["bot_dimensions"]:
        data["deviceOS"] = h.metadata.swarming_result["bot_dimensions"]["device_os"]

    data["iteration"] = h.metadata.attemptNo
    data["jobID"] = job.job_id
    data["metric"] = h["name"]
    data["story"] = job.benchmark_arguments.story # TODO: What if user used story tags?
    data["value"] = h["sampleValues"][0]
    data["passing"] = True # TODO: How do we figure this out?

    print("\n\n" + data + "\n\n")


    #rows.append(big_query_utils.make_row())
    #if not big_query_utils.insert_rows(bq, _PROJECT_ID, _DATASET,
    #                                   _TABLE,
    #                                    rows):
    #  logging.error('Error when uploading results')

