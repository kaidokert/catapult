# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime

from dashboard.common import report_query
from dashboard.models import report_template


REPORTS = [
    ('Chrome', 'Android Go', 'perf-go-phone-1024'),
    ('Chrome', 'Nexus 5', 'health-plan-clankium-phone'),
    ('WebView', 'Android Go', 'perf-go-webview-phone'),
    ('WebView', 'Nexus 5', 'health-plan-webview-phone')
]

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


def GetTemplate(browser, builder):
  bot = ':'.join(['ClankInternal', builder])
  return {
      'rows': list(IterTemplateRows(browser, bot)),
      'statistics': ['avg', 'std', 'max']
  }


def GetReportTemplates():
  reports = []
  for browser, device, builder in REPORTS:
    reports.append({
        'name': ':'.join(['Health', browser, device]),
        'template': GetTemplate(browser.lower(), builder),
        'internal_only': False
    })
  return reports


@report_template.Static(
    internal_only=False,
    template_id='health-chrome-go',
    name='Health:Chrome:Android Go',
    modified=datetime.datetime(2018, 8, 2))
def ChromeAndroidGo(revisions):
  template = GetTemplate('chrome', 'perf-go-phone-1024')
  return report_query.ReportQuery(template, revisions)


@report_template.Static(
    internal_only=False,
    template_id='health-chrome-n5',
    name='Health:Chrome:Nexus 5',
    modified=datetime.datetime(2018, 8, 2))
def ChromeNexus5(revisions):
  template = GetTemplate('chrome', 'health-plan-clankium-phone')
  return report_query.ReportQuery(template, revisions)


@report_template.Static(
    internal_only=False,
    template_id='health-webview-go',
    name='Health:WebView:Android Go',
    modified=datetime.datetime(2018, 8, 2))
def WebViewAndroidGo(revisions):
  template = GetTemplate('webview', 'perf-go-webview-phone')
  return report_query.ReportQuery(template, revisions)


@report_template.Static(
    internal_only=False,
    template_id='health-webview-n5',
    name='Health:WebView:Nexus 5',
    modified=datetime.datetime(2018, 8, 2))
def WebViewNexus5(revisions):
  template = GetTemplate('webview', 'health-plan-webview-phone')
  return report_query.ReportQuery(template, revisions)
