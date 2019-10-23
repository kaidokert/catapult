# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import random
import sys
import uuid

from py_utils import cloud_storage  # pylint: disable=import-error

from tracing.trace_data import trace_data

HTML_TRACE_NAME = 'trace.html'

_TEN_MINUTES = 60*10


#TODO(crbug.com/772216): Remove this once the uploading is done by Chromium
# test recipe.
def UploadArtifactsToCloud(results):
  """Upload all artifacts of the test to cloud storage.

  Sets 'url' attribute of each artifact to its cloud URL.
  """
  for run in results.IterStoryRuns():
    for artifact in run.IterArtifacts():
      if artifact.url is None:
        remote_name = str(uuid.uuid1())
        cloud_url = cloud_storage.Insert(
            results.upload_bucket, remote_name, artifact.local_path)
        logging.info('Uploading %s of page %s to %s\n' % (
            artifact.name, run.story.name, cloud_url))
        artifact.SetUrl(cloud_url)


def SerializeAndUploadHtmlTraces(results):
  """Creates and uploads html trace files for each story run, if necessary.

  For each story run, takes all trace files from individual trace agents
  and runs trace2html on them. Then uploads the resulting html to cloud.
  This is done only once, subsequent calls to this function will not
  do anything.
  """
  for run in results.IterRunsWithTraces():
    _SerializeAndUploadHtmlTrace(run, results.label, results.upload_bucket)


def _TraceCanonicalName(run, label):
  parts = [
      run.story.file_safe_name,
      label,
      run.start_datetime.strftime('%Y-%m-%d_%H-%M-%S'),
      random.randint(1, 1e5)]
  return '_'.join(str(p) for p in parts if p) + '.html'


def _SerializeAndUploadHtmlTrace(run, label, bucket):
  html_trace = run.GetArtifact(HTML_TRACE_NAME)
  if html_trace is None:
    trace_files = [art.local_path for art in run.IterArtifacts('trace')]
    with run.CaptureArtifact(HTML_TRACE_NAME) as html_path:
      trace_data.SerializeAsHtml(trace_files, html_path)

  html_trace = run.GetArtifact(HTML_TRACE_NAME)
  if bucket is not None and html_trace.url is None:
    remote_name = _TraceCanonicalName(run, label)
    cloud_url = cloud_storage.Insert(bucket, remote_name, html_trace.local_path)
    sys.stderr.write(
        'View generated trace files online at %s for story %s\n' % (
            cloud_url, run.story.name))
    html_trace.SetUrl(cloud_url)

  return html_trace
