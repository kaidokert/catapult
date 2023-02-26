# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import

import logging
import time
from google.appengine.api import app_identity
from google.cloud import monitoring_v3

METRIC_TYPE_PREFIX = "custom.googleapis.com/"
PROJECT_ID = "chromeperf"
RESOURCE_TYPE = "generic_task"
LOCATION = "us-central1"
NAMESPACE = "Prod"
DEFAULT_TASK_ID = "task_id"
JOB_ID = "job_id"
JOB_TYPE = "job_type"
JOB_STATUS = "job_status"
API_METRIC_TYPE = "api/metrics"
API_NAME = "api_name"
REQUEST_STATUS = "request_status"


def PublishPinpointJobStatusMetric(stage,
                                   job_id,
                                   job_type,
                                   job_status,
                                   metric_value=1):
  label_dict = {JOB_ID: job_id, JOB_TYPE: job_type, JOB_STATUS: job_status}
  PublishTSCloudMetric("pinpoint", "pinpoint/job/status_change", label_dict,
                       stage, metric_value)


def PublishPinpointJobRunTimeMetric(stage, job_id, job_type, job_status,
                                    metric_value):
  label_dict = {JOB_ID: job_id, JOB_TYPE: job_type, JOB_STATUS: job_status}
  PublishTSCloudMetric("pinpoint", "pinpoint/job/run_time", label_dict, stage,
                       metric_value)


def PublishTSCloudMetric(service_name,
                         metric_type,
                         label_dict,
                         stage=NAMESPACE,
                         metric_value=1):
  client = monitoring_v3.MetricServiceClient()
  project_name = f"projects/{PROJECT_ID}"

  series = monitoring_v3.TimeSeries()

  series.metric.type = METRIC_TYPE_PREFIX + metric_type

  series.resource.type = RESOURCE_TYPE

  # The identifier of the GCP project associated with this resource, such as "my-project".
  series.resource.labels["project_id"] = PROJECT_ID

  # The GCP region in which data about the resource is stored
  series.resource.labels["location"] = LOCATION

  # A namespace identifier, such as a cluster name: Dev, Staging or Prod
  series.resource.labels["namespace"] = stage

  # An identifier for a grouping of related tasks, such as the name of a microservice or
  # distributed batch job
  series.resource.labels["job"] = service_name

  # A unique identifier for the task within the namespace and job, set default value for
  # this manditory field
  series.resource.labels["task_id"] = DEFAULT_TASK_ID

  for key in label_dict:
    series.metric.labels[key] = label_dict[key]

  now = time.time()
  seconds = int(now)
  nanos = int((now - seconds) * 10**9)
  interval = monitoring_v3.TimeInterval(
      {"end_time": {
          "seconds": seconds,
          "nanos": nanos
      }})
  point = monitoring_v3.Point({
      "interval": interval,
      "value": {
          "double_value": metric_value
      }
  })
  series.points = [point]
  client.create_time_series(name=project_name, time_series=[series])


class APIMetricLogger:

  def __init__(self, service_name, api_name):
    self._service_name = service_name
    self._api_name = api_name
    self._start = None
    self.seconds = 0

  def _Now(self):
    return time.time()

  def __enter__(self):
    self._start = self._Now()
    label_dict = {API_NAME: self._api_name, REQUEST_STATUS: "started"}
    PublishTSCloudMetric(self._service_name, API_METRIC_TYPE, label_dict,
                         app_identity.get_application_id())

  def __exit__(self, type, value, traceback):
    if type is None:
      # run succeed
      self.seconds = self._Now() - self._start
      logging.info('%s:%s=%f', self._service_name, self._api_name, self.seconds)
      label_dict = {REQUEST_STATUS: "completed"}
      PublishTSCloudMetric(self._service_name, API_METRIC_TYPE, label_dict,
                           app_identity.get_application_id(), self.seconds)
    else:
      # has exception
      label_dict = {API_NAME: self._api_name, REQUEST_STATUS: "failed"}
      PublishTSCloudMetric(self._service_name, API_METRIC_TYPE, label_dict,
                           app_identity.get_application_id())
      # throw out the exception
      return False


def APIMetric(label):

  def Decorator(wrapped):

    def Wrapper(*a, **kw):
      with APIMetricLogger(label):
        return wrapped(*a, **kw)

    return Wrapper

  return Decorator
