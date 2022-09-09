# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Dispatches requests to request handler classes."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import six
import logging

from dashboard import alerts
from dashboard import edit_site_config
from dashboard import graph_csv
from dashboard import main
from dashboard import navbar
from dashboard import sheriff_config_poller

from flask import Flask
flask_app = Flask(__name__)


@flask_app.route('/alerts', methods=['GET'])
def AlertsHandlerGet():
  return alerts.AlertsHandlerGet()


@flask_app.route('/alerts', methods=['POST'])
def AlertsHandlerPost():
  return alerts.AlertsHandlerPost()


@flask_app.route('/edit_site_config', methods=['GET'])
def EditSiteConfigHandlerGet():
  return edit_site_config.EditSiteConfigHandlerGet()


@flask_app.route('/edit_site_config', methods=['POST'])
def EditSiteConfigHandlerPost():
  return edit_site_config.EditSiteConfigHandlerPost()


@flask_app.route('/graph_csv', methods=['GET'])
def GraphCSVHandlerGet():
  return graph_csv.GraphCSVGet()


@flask_app.route('/graph_csv', methods=['POST'])
def GraphCSVHandlerPost():
  return graph_csv.GraphCSVPost()


@flask_app.route('/')
def MainHandlerGet():
  return main.MainHandlerGet()


@flask_app.route('/navbar')
def NavbarHandlerPost():
  return navbar.NavbarHandlerPost()


@flask_app.route('/configs/update')
def SheriffConfigPollerGet():
  return sheriff_config_poller.SheriffConfigPollerGet()


if six.PY2:
  import gae_ts_mon
  import webapp2

  # pylint: disable=ungrouped-imports
  from dashboard import add_histograms
  from dashboard import add_histograms_queue
  from dashboard import add_point
  from dashboard import add_point_queue
  from dashboard import alert_groups
  from dashboard import associate_alerts
  from dashboard import bug_details
  from dashboard import buildbucket_job_status
  from dashboard import create_health_report
  from dashboard import dump_graph_json
  from dashboard import edit_anomalies
  from dashboard import edit_anomaly_configs
  from dashboard import edit_bug_labels
  from dashboard import file_bug
  from dashboard import get_diagnostics
  from dashboard import get_histogram
  from dashboard import graph_json
  from dashboard import graph_revisions
  from dashboard import group_report
  from dashboard import jstsmon
  from dashboard import layered_cache_delete_expired
  from dashboard import list_tests
  from dashboard import load_from_prod
  from dashboard import mark_recovered_alerts
  from dashboard import memory_report
  from dashboard import migrate_test_names
  from dashboard import oauth2_decorator
  from dashboard import pinpoint_request
  from dashboard import put_entities_task
  from dashboard import report
  from dashboard import short_uri
  from dashboard import speed_releasing
  from dashboard import update_dashboard_stats
  from dashboard import update_test_suite_descriptors
  from dashboard import update_test_suites
  from dashboard import uploads_info
  from dashboard.api import alerts as api_alerts
  from dashboard.api import bugs
  from dashboard.api import config
  from dashboard.api import describe
  from dashboard.api import list_timeseries
  from dashboard.api import new_bug
  from dashboard.api import new_pinpoint
  from dashboard.api import existing_bug
  from dashboard.api import nudge_alert
  from dashboard.api import report_generate
  from dashboard.api import report_names
  from dashboard.api import report_template
  from dashboard.api import test_suites
  from dashboard.api import timeseries
  from dashboard.api import timeseries2

  _URL_MAPPING = [
      ('/_/jstsmon', jstsmon.JsTsMonHandler),
      ('/add_histograms', add_histograms.AddHistogramsHandler),
      ('/add_histograms/process', add_histograms.AddHistogramsProcessHandler),
      ('/add_histograms_queue', add_histograms_queue.AddHistogramsQueueHandler),
      ('/add_point', add_point.AddPointHandler),
      ('/add_point_queue', add_point_queue.AddPointQueueHandler),
      ('/alerts', alerts.AlertsHandler),
      (r'/api/alerts', api_alerts.AlertsHandler),
      (r'/api/bugs/p/(.+)/(.+)', bugs.BugsWithProjectHandler),
      (r'/api/bugs/(.*)', bugs.BugsHandler),
      (r'/api/config', config.ConfigHandler),
      (r'/api/describe', describe.DescribeHandler),
      (r'/api/list_timeseries/(.*)', list_timeseries.ListTimeseriesHandler),
      (r'/api/new_bug', new_bug.NewBugHandler),
      (r'/api/new_pinpoint', new_pinpoint.NewPinpointHandler),
      (r'/api/existing_bug', existing_bug.ExistingBugHandler),
      (r'/api/nudge_alert', nudge_alert.NudgeAlertHandler),
      (r'/api/report/generate', report_generate.ReportGenerateHandler),
      (r'/api/report/names', report_names.ReportNamesHandler),
      (r'/api/report/template', report_template.ReportTemplateHandler),
      (r'/api/test_suites', test_suites.TestSuitesHandler),
      (r'/api/timeseries/(.*)', timeseries.TimeseriesHandler),
      (r'/api/timeseries2', timeseries2.Timeseries2Handler),
      ('/associate_alerts', associate_alerts.AssociateAlertsHandler),
      ('/alert_groups_update', alert_groups.AlertGroupsHandler),
      ('/bug_details', bug_details.BugDetailsHandler),
      (r'/buildbucket_job_status/(\d+)',
       buildbucket_job_status.BuildbucketJobStatusHandler),
      ('/create_health_report', create_health_report.CreateHealthReportHandler),
      ('/configs/update', sheriff_config_poller.ConfigsUpdateHandler),
      ('/delete_expired_entities',
       layered_cache_delete_expired.LayeredCacheDeleteExpiredHandler),
      ('/dump_graph_json', dump_graph_json.DumpGraphJsonHandler),
      ('/edit_anomalies', edit_anomalies.EditAnomaliesHandler),
      ('/edit_anomaly_configs', edit_anomaly_configs.EditAnomalyConfigsHandler),
      ('/edit_bug_labels', edit_bug_labels.EditBugLabelsHandler),
      ('/edit_site_config', edit_site_config.EditSiteConfigHandler),
      ('/file_bug', file_bug.FileBugHandler),
      ('/get_diagnostics', get_diagnostics.GetDiagnosticsHandler),
      ('/get_histogram', get_histogram.GetHistogramHandler),
      ('/graph_csv', graph_csv.GraphCsvHandler),
      ('/graph_json', graph_json.GraphJsonHandler),
      ('/graph_revisions', graph_revisions.GraphRevisionsHandler),
      ('/group_report', group_report.GroupReportHandler),
      ('/list_tests', list_tests.ListTestsHandler),
      ('/load_from_prod', load_from_prod.LoadFromProdHandler),
      ('/', main.MainHandler),
      ('/mark_recovered_alerts',
       mark_recovered_alerts.MarkRecoveredAlertsHandler),
      ('/memory_report', memory_report.MemoryReportHandler),
      ('/migrate_test_names', migrate_test_names.MigrateTestNamesHandler),
      ('/navbar', navbar.NavbarHandler),
      ('/pinpoint/new/bisect',
       pinpoint_request.PinpointNewBisectRequestHandler),
      ('/pinpoint/new/perf_try',
       pinpoint_request.PinpointNewPerfTryRequestHandler),
      ('/pinpoint/new/prefill',
       pinpoint_request.PinpointNewPrefillRequestHandler),
      ('/put_entities_task', put_entities_task.PutEntitiesTaskHandler),
      ('/report', report.ReportHandler),
      ('/short_uri', short_uri.ShortUriHandler),
      (r'/speed_releasing/(.*)', speed_releasing.SpeedReleasingHandler),
      ('/speed_releasing', speed_releasing.SpeedReleasingHandler),
      ('/update_dashboard_stats',
       update_dashboard_stats.UpdateDashboardStatsHandler),
      ('/update_test_suites', update_test_suites.UpdateTestSuitesHandler),
      ('/update_test_suite_descriptors',
       update_test_suite_descriptors.UpdateTestSuiteDescriptorsHandler),
      ('/uploads/(.+)', uploads_info.UploadInfoHandler),
      (oauth2_decorator.DECORATOR.callback_path,
       oauth2_decorator.DECORATOR.callback_handler())
  ]

  webapp2_app = webapp2.WSGIApplication(_URL_MAPPING, debug=False)
  gae_ts_mon.initialize(webapp2_app)

# After a handler is migrated to flask, add its handled url here.
# The listed values will be used as *prefix* to match and redirect
# the incoming requests.
_PATHS_HANDLED_BY_FLASK = [
    # '/alerts',
    # '/configs/update',
    # '/edit_site_config',
    # '/graph_csv',
    # '/navbar',
]


def IsPathHandledByFlask(path):
  # the main hanlder cannot use startswith(). Full match here.
  if path == '/':
    return True
  return any(path.startswith(p) for p in _PATHS_HANDLED_BY_FLASK)


def APP(environ, request):
  path = environ.get('PATH_INFO', '')
  method = environ.get('REQUEST_METHOD', '')
  logging.info('Request path from environ: %s. Method: %s', path, method)

  if IsPathHandledByFlask(path):
    logging.debug('Handled by flask.')
    return flask_app(environ, request)

  logging.debug('Handled by webapp2')
  return webapp2_app(environ, request)
