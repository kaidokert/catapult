# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import random
import sys
import time
import uuid

from py_utils import cloud_storage  # pylint: disable=import-error

from telemetry.value import common_value_helpers
from tracing.metrics import metric_runner
from tracing.trace_data import trace_data

HTML_TRACE_NAME = 'trace.html'

_TEN_MINUTES = 60*10


def UploadArtifactsToCloud(run, bucket):
  for artifact in run.IterArtifacts():
    if artifact.url is None:
      remote_name = str(uuid.uuid1())
      cloud_url = cloud_storage.Insert(bucket, remote_name, artifact.local_path)
      logging.info('Uploading %s of page %s to %s\n' % (
          artifact.name, run.story.name, cloud_url))
      artifact.SetUrl(cloud_url)


def TraceCanonicalName(run, label):
  parts = [
      run.story.file_safe_name,
      label,
      run.start_datetime.strftime('%Y-%m-%d_%H-%M-%S'),
      random.randint(1, 1e5)]
  return '_'.join(str(p) for p in parts if p) + '.html'


def SerializeAndUploadHtmlTrace(run, label, bucket):
  html_trace = run.GetArtifact(HTML_TRACE_NAME)
  if html_trace is None:
    trace_files = [art.local_path for art in run.IterArtifacts('trace')]
    with run.CaptureArtifact(HTML_TRACE_NAME) as html_path:
      trace_data.SerializeAsHtml(trace_files, html_path)

  html_trace = run.GetArtifact(HTML_TRACE_NAME)
  if bucket is not None and html_trace.url is None:
    remote_name = TraceCanonicalName(run, label)
    cloud_url = cloud_storage.Insert(bucket, remote_name, html_trace.local_path)
    sys.stderr.write(
        'View generated trace files online at %s for story %s\n' % (
            cloud_url, run.story.name))
    html_trace.SetUrl(cloud_url)

  return html_trace


def ComputeMetricsInPool(run, label, bucket):
  story_name = run.story.name
  try:
    retvalue = {
        'run': run,
        'fail': [],
        'histogram_dicts': None,
        'scalars': []
    }
    extra_import_options = {
        'trackDetailedModelStats': True
    }

    html_trace = SerializeAndUploadHtmlTrace(run, label, bucket)
    trace_size_in_mib = os.path.getsize(html_trace.local_path) / (2 ** 20)
    # Bails out on trace that are too big. See crbug.com/812631 for more
    # details.
    if trace_size_in_mib > 400:
      retvalue['fail'].append(
          '%s: Trace size is too big: %s MiB' % (story_name, trace_size_in_mib))
      return retvalue

    logging.info('%s: Starting to compute metrics on trace.', story_name)
    start = time.time()
    # This timeout needs to be coordinated with the Swarming IO timeout for the
    # task that runs this code. If this timeout is longer or close in length
    # to the swarming IO timeout then we risk being forcibly killed for not
    # producing any output. Note that this could be fixed by periodically
    # outputing logs while waiting for metrics to be calculated.
    timeout = _TEN_MINUTES
    mre_result = metric_runner.RunMetricOnSingleTrace(
        html_trace.local_path, run.tbm_metrics,
        extra_import_options, canonical_url=html_trace.url,
        timeout=timeout)
    logging.info('%s: Computing metrics took %.3f seconds.' % (
        story_name, time.time() - start))

    if mre_result.failures:
      for f in mre_result.failures:
        retvalue['fail'].append('%s: %s' % (story_name, str(f)))

    histogram_dicts = mre_result.pairs.get('histograms', [])
    retvalue['histogram_dicts'] = histogram_dicts

    scalars = []
    for d in mre_result.pairs.get('scalars', []):
      scalars.append(common_value_helpers.TranslateScalarValue(
          d, run.story))
    retvalue['scalars'] = scalars
    return retvalue
  except Exception as e:  # pylint: disable=broad-except
    # logging exception here is the only way to get a stack trace since
    # multiprocessing's pool implementation does not save that data. See
    # crbug.com/953365.
    logging.error('%s: Exception while calculating metric', story_name)
    logging.exception(e)
    raise
