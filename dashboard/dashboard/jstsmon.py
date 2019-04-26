# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from gae_ts_mon import CumulativeDistributionMetric
from gae_ts_mon import MetricsDataUnits
from gae_ts_mon.handlers import TSMonJSHandler


METRICS = [
    CumulativeDistributionMetric(
        'chromeperf/load/page',
        'page loadEventEnd - fetchStart',
        units=MetricsDataUnits.MILLISECONDS,
        field_spec=[]),
    CumulativeDistributionMetric(
        'chromeperf/load/chart',
        'chart load latency',
        units=MetricsDataUnits.MILLISECONDS,
        field_spec=[]),
    CumulativeDistributionMetric(
        'chromeperf/load/alerts',
        'alerts load latency',
        units=MetricsDataUnits.MILLISECONDS,
        field_spec=[]),
    CumulativeDistributionMetric(
        'chromeperf/action/triage',
        'alert triage latency',
        units=MetricsDataUnits.MILLISECONDS,
        field_spec=[]),
    CumulativeDistributionMetric(
        'chromeperf/load/menu',
        'timeseries picker menu latency',
        units=MetricsDataUnits.MILLISECONDS,
        field_spec=[]),
    CumulativeDistributionMetric(
        'chromeperf/action/chart',
        'timeseries picker activity duration',
        units=MetricsDataUnits.MILLISECONDS,
        field_spec=[]),
]


class JsTsMonHandler(TSMonJSHandler):

  def __init__(self, request=None, response=None):
    super(JsTsMonHandler, self).__init__(request, response)
    self.register_metrics(METRICS)

  def xsrf_is_valid(self, unused_body):  # pylint: disable=invalid-name
    return True
