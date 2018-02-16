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
# TODO(crbug.com/736506): For Chrome metrics we ideally want to alert on
# allocated_objects_size rather than effective_size, since the former tends to
# be a more stable metric. However, not all allocators report allocated_objects
# and some teams (e.g. v8) want to keep effective_size alerts regardless.
CHROME_ALLOCATED = MemoryAlert(reported_by='chrome', size='allocated_objects')
CHROME_EFFECTIVE = MemoryAlert(reported_by='chrome', size='effective')
OS_METRIC = MemoryAlert(reported_by='os', size='proportional_resident')

# Common metrics to alert on for all desktop and mobile configurations.
DEFAULT_ALERTS = (
    # Metrics reporting allocated_objects.
    CHROME_ALLOCATED.Clone(allocator='java_heap', config='memory_above_1m'),
    CHROME_ALLOCATED.Clone(allocator='malloc'),
    CHROME_ALLOCATED.Clone(allocator='v8'),
    # Metrics with no allocated_objects or where we also want effective_size.
    CHROME_EFFECTIVE.Clone(allocator='cc'),
    CHROME_EFFECTIVE.Clone(allocator='gpu'),
    CHROME_EFFECTIVE.Clone(allocator='malloc'),
    CHROME_EFFECTIVE.Clone(allocator='skia'),
    CHROME_EFFECTIVE.Clone(allocator='v8'),
    # Our top-level source of truth.
    OS_METRIC.Clone(allocator='system_memory', size='private_footprint'),
)

# Extra metrics to alert on for Android System Health reporting purposes.
ANDROID_ALERTS = (
    # Java Heap
    OS_METRIC.Clone(allocator='system_memory:java_heap',
                    config='memory_above_1m'),
    # Native Heap
    OS_METRIC.Clone(allocator='system_memory:native_heap'),
    # Private Dirty
    OS_METRIC.Clone(allocator='system_memory', size='private_dirty'),
    # Android Graphics
    OS_METRIC.Clone(allocator='gpu_memory'),
    # Overall PSS
    OS_METRIC.Clone(allocator='system_memory'),
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
      for alert in DEFAULT_ALERTS + ANDROID_ALERTS:
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
