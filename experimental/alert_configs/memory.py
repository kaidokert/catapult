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


_MemoryAlert = collections.namedtuple('MemoryAlert', [
    'master', 'builder', 'benchmark', 'browser', 'process', 'probe', 'story',
    'config'])


class MemoryAlert(_MemoryAlert):
  __slots__ = ()

  def __new__(cls, probe, **kwargs):
    kwargs['probe'] = probe
    kwargs.setdefault('master', 'ChromiumPerf')
    kwargs.setdefault('builder', '*')
    kwargs.setdefault('benchmark', '*')
    kwargs.setdefault('browser', 'chrome')
    kwargs.setdefault('process', 'all_processes')
    kwargs.setdefault('story', '*/*')
    kwargs.setdefault('config', 'memory_above_64k')
    return super(cls, MemoryAlert).__new__(cls, **kwargs)

  def __str__(self):
    return '/'.join([self.master, self.builder, self.benchmark, self.metric,
                     self.story])

  @property
  def metric(self):
    return 'memory:%s:%s:reported_%s_avg' % (
        self.browser, self.process, self.probe)

  def Clone(self, **kwargs):
    """Make a copy of this alert with some fields updated."""
    return self._replace(**kwargs)


# Common metrics to alert on for all desktop and mobile configurations.
DEFAULT_ALERTS = [
    MemoryAlert('by_chrome:cc:effective_size'),
    MemoryAlert('by_chrome:gpu:effective_size'),
    MemoryAlert('by_chrome:java_heap:effective_size', config='memory_above_1m'),
    MemoryAlert('by_chrome:malloc:effective_size'),
    MemoryAlert('by_chrome:skia:effective_size'),
    MemoryAlert('by_chrome:v8:effective_size'),
    MemoryAlert('by_os:system_memory:private_footprint_size'),
]

# Extra metrics to alert on for Android System Health reporting purposes.
ANDROID_ALERTS = [
    MemoryAlert('by_os:system_memory:proportional_resident_size'),
    MemoryAlert('by_os:system_memory:private_dirty_size'),
    MemoryAlert('by_os:system_memory:java_heap:proportional_resident_size',
                config='memory_above_1m'),
    MemoryAlert('by_os:system_memory:native_heap:proportional_resident_size'),
    MemoryAlert('by_os:gpu_memory:proportional_resident_size'),
]


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
