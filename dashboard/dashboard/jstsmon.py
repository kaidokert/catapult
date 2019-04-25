# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from gae_ts_mon import CumulativeDistributionMetric
from gae_ts_mon import MetricsDataUnits
from gae_ts_mon.handlers import TSMonJSHandler


METRIC_NAMES = {
    'fetch': ['ConfigRequest', 'TestSuitesRequest'],
    'load': ['fetchStart', 'domainLookupStart', 'domainLookupEnd'],
}

METRICS = []
for group, names in METRIC_NAMES.items():
  for name in names:
    METRICS.append(CumulativeDistributionMetric(
        'chromeperf2/%s/%s' % (group, name),
        '%s %s',
        units=MetricsDataUnits.MILLISECONDS,
        field_spec=[]))


class JsTsMonHandler(TSMonJSHandler):

  def __init__(self, request=None, response=None):
    super(JsTsMonHandler, self).__init__(request, response)
    self.register_metrics(METRICS)

  def xsrf_is_valid(self, unused_body):  # pylint: disable=invalid-name
    return True
