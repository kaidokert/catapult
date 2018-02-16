#!/usr/bin/env python
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""
Run this script to generate the alert configs for memory benchmarks and
metrics to keep track of.

After making changes to this script make sure to actually update the
configs at: https://chromeperf.appspot.com/edit_anomaly_configs
"""
import collections


_MemoryAlert = collections.namedtuple('_MemoryAlert', [
    'master', 'builder', 'benchmark', 'browser', 'process',
    'reported_by', 'allocator', 'size', 'story', 'config'])


class MemoryAlert(_MemoryAlert):
  __slots__ = ()

  def __new__(cls, **kwargs):
    kwargs.setdefault('master', 'ChromiumPerf')
    kwargs.setdefault('builder', '*')
    kwargs.setdefault('benchmark', '*')
    kwargs.setdefault('browser', 'chrome')
    kwargs.setdefault('process', 'all_processes')
    kwargs.setdefault('reported_by', '*')
    kwargs.setdefault('allocator', '*')
    kwargs.setdefault('size', '*')
    kwargs.setdefault('story', '*/*')
    kwargs.setdefault('config', 'memory_above_64k')
    return super(cls, MemoryAlert).__new__(cls, **kwargs)

  def __str__(self):
    return '/'.join([self.master, self.builder, self.benchmark, self.metric,
                     self.story])

  @property
  def metric(self):
    return 'memory:%s:%s:reported_by_%s:%s:%s_size_avg' % (
        self.browser, self.process, self.reported_by, self.allocator,
        self.size)

  def Clone(self, **kwargs):
    """Make a copy of this alert with some fields updated."""
    return super(MemoryAlert, self)._replace(**kwargs)


# Default settings for metrics reported by Chrome and OS probes.
# For Chrome metrics by default we alert on allocated_objects, as those tend
# to produce more stable measurements. See crbug.com/736506.
CHROME_METRIC = MemoryAlert(reported_by='chrome', size='allocated_objects')
OS_METRIC = MemoryAlert(reported_by='os', size='proportional_resident')

# Common metrics to alert on for all desktop and mobile configurations.
DEFAULT_ALERTS = (
    CHROME_METRIC.Clone(allocator='cc'),
    CHROME_METRIC.Clone(allocator='gpu'),
    CHROME_METRIC.Clone(allocator='java_heap', config='memory_above_1m'),
    CHROME_METRIC.Clone(allocator='malloc'),
    CHROME_METRIC.Clone(allocator='skia'),
    CHROME_METRIC.Clone(allocator='v8'),
    # For some allocators we want to alert on effective_size too.
    CHROME_METRIC.Clone(allocator='malloc', size='effective'),
    CHROME_METRIC.Clone(allocator='v8', size='effective'),
    # Our top-level source of truth.
    OS_METRIC.Clone(allocator='system_memory', size='private_footprint'),
)

# Extra metrics to alert on for Android System Health reporting purposes.
ANDROID_ALERTS = (
    OS_METRIC.Clone(allocator='system_memory'),
    OS_METRIC.Clone(allocator='system_memory', size='private_dirty'),
    OS_METRIC.Clone(allocator='system_memory:java_heap',
                    config='memory_above_1m'),
    OS_METRIC.Clone(allocator='system_memory:native_heap'),
    OS_METRIC.Clone(allocator='gpu_memory'),
)


def main():
  alerts = []

  ## Desktop ##

  # Alerts for system_health.memory_desktop.
  for alert in DEFAULT_ALERTS:
    alerts.append(alert.Clone(benchmark='system_health.memory_desktop'))

  # Alerts for memory.desktop.
  for alert in DEFAULT_ALERTS:
    alerts.append(alert.Clone(benchmark='memory.desktop', story='*'))

  ## Mobile ##

  # Alerts for system_health.memory_mobile.
  for master in ('ChromiumPerf', 'ClankInternal'):
    for browser in ('chrome', 'webview'):
      for alert in DEFAULT_ALERTS:
        alerts.append(alert.Clone(
            benchmark='system_health.memory_mobile',
            master=master, browser=browser))

  # Alerts for memory.top_10_mobile.
  for master in ('ChromiumPerf', 'ClankInternal'):
    for browser in ('chrome', 'webview'):
      for alert in DEFAULT_ALERTS + ANDROID_ALERTS:
        alerts.append(alert.Clone(
            benchmark='memory.top_10_mobile', master=master, browser=browser))

  # Alerts for memory.dual_browser_test.
  for browser in ('chrome', 'webview'):
    for alert in DEFAULT_ALERTS:
      alerts.append(alert.Clone(
          benchmark='memory.dual_browser_test',
          master='ClankInternal', browser=browser))


  # Group alerts by config and print them.
  by_config = collections.defaultdict(list)
  for alert in alerts:
    by_config[alert.config].append(alert)

  for config, group in sorted(by_config.iteritems()):
    print '#', config
    for alert in group:
      print alert
    print


if __name__ == '__main__':
  main()
