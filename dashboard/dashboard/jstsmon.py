# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from gae_ts_mon import CumulativeDistributionMetric
from gae_ts_mon import MetricsDataUnits
from gae_ts_mon.handlers import TSMonJSHandler


METRICS = {}


class JsTsMonHandler(TSMonJSHandler):

  def __init__(self, request=None, response=None):
    super(JsTsMonHandler, self).__init__(request, response)
    self._metrics = True  # cheese self.post()

  def xsrf_is_valid(self, body):  # pylint: disable=invalid-name
    for metric_measurement in body.get('metrics', []):
      name = metric_measurement['MetricInfo']['Name']
      if name not in METRICS:
        METRICS[name] = CumulativeDistributionMetric(
            name, name,
            units=MetricsDataUnits.MILLISECONDS,
            field_spec=[])
    if self._metrics is True:
      self._metrics = None
    self.register_metrics(METRICS.values())
    return True
