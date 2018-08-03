# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime

from dashboard.common import report_query
from dashboard.models import report_template


# TODO(perezju): Use FetchCachedTestSuiteDescriptor() in
# update_test_suite_descriptors to dynamically get these.
MEMORY_PHASES = [
    ('Foreground', ['load:*', 'browse:*']),
    ('Background', ['background:*'])
]

MEMORY_METRICS = [
    ('Java Heap', 'system_memory:java_heap'),
    ('Native Heap', 'system_memory:native_heap'),
    ('Android Graphics', 'gpu_memory'),
    ('Overall PSS', 'system_memory')
]

STARTUP_BY_BROWSER = {
    'chrome': {
        'testSuites': ['start_with_url.cold.startup_pages'],
        'measurement': 'foreground_tab_request_start',
        'testCases': ['http://bbc.co.uk']
    },
    'webview': {
        'testSuites': ['system_health.webview_startup'],
        'measurement': 'webview_startup_wall_time_avg',
        'testCases': ['load:chrome:blank']
    }
}


def IterTemplateRows(browser, bot):
  for phase, test_cases in MEMORY_PHASES:
    for label, component in MEMORY_METRICS:
      yield {
          'label': ':'.join([phase, label]),
          'testSuites': ['system_health.memory_mobile'],
          'bots': [bot],
          'measurement': ':'.join([
              'memory', browser, 'all_processes:reported_by_os', component,
              'proportional_resident_size']),
          'testCases': test_cases
      }
  yield {
      'label': 'Battery:Energy Consumption',
      'testSuites': ['power.typical_10_mobile'],
      'bots': [bot],
      'measurement': 'application_energy_consumption_mwh',
      'testCases': []
  }
  yield dict(STARTUP_BY_BROWSER[browser], label='Startup:Time', bots=[bot])


def CreateSystemHealthReport(template_id, name, builder, modified):
  # The browser (Chrome/WebView) is always the second part of the report name,
  # and is used to build the right template.
  browser = name.split(':')[1].lower()
  bot = ':'.join(['ClankInternal', builder])
  template = {
      'rows': list(IterTemplateRows(browser, bot)),
      'statistics': ['avg', 'std', 'max']
  }

  # pylint: disable=unused-variable

  # TODO(perezju): Consider whether we might point to more relevant docs.
  documentation_url = 'https://bit.ly/system-health-benchmarks'

  @report_template.Static(
      template_id=template_id,
      name=name,
      internal_only=False,
      modified=modified)
  def Report(revisions):
    return report_query.ReportQuery(template, revisions)


CreateSystemHealthReport(
    template_id=2013652838,
    name='Health:Chrome:Android Go',
    builder='perf-go-phone-1024',
    modified=datetime.datetime(2018, 8, 2))

CreateSystemHealthReport(
    template_id=434658613,
    name='Health:Chrome:Nexus 5',
    builder='health-plan-clankium-phone',
    modified=datetime.datetime(2018, 8, 2))

CreateSystemHealthReport(
    template_id=1371943537,
    name='Health:WebView:Android Go',
    builder='perf-go-webview-phone',
    modified=datetime.datetime(2018, 8, 2))

CreateSystemHealthReport(
    template_id=191176182,
    name='Health:WebView:Nexus 5',
    builder='health-plan-webview-phone',
    modified=datetime.datetime(2018, 8, 2))
