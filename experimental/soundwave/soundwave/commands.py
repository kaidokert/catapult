# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from soundwave import models
from soundwave import dashboard_api
from soundwave import database


def FetchAlertsData(args):
  dashboard_communicator = dashboard_api.PerfDashboardCommunicator(args)
  alerts = dashboard_communicator.GetAlertData(
      args.benchmark, args.days)['anomalies']
  print '%s alerts found!' % len(alerts)

  bug_ids = set()
  with database.Database(args.database_file) as db:
    with db.Transaction():
      for alert in alerts:
        alert = models.Alert.FromJson(alert)
        db.Put(alert)
        if alert.bug_id is not None:
          bug_ids.add(alert.bug_id)

    total_bugs = len(bug_ids)
    if args.reuse_cached_items:
      bug_ids = [i for i in bug_ids if not db.Find(models.Bug, id=i)]
      print 'Collecting data for %d remaining out of %d bugs.' % (
          len(bug_ids), total_bugs)
    else:
      print 'Collecting and updating data for %d bugs.' % total_bugs

    for bug_id in bug_ids:
      data = dashboard_communicator.GetBugData(bug_id)
      bug = models.Bug.FromJson(data['bug'])
      db.Put(bug, commit=True)


def FetchTimeseriesData(args):
  dashboard_communicator = dashboard_api.PerfDashboardCommunicator(args)
  with database.Database(args.database_file) as db:
    # TODO(#4349): Fetch timeseries in parallel and with shorter tansactions.
    with db.Transaction():
      for point_data in dashboard_communicator.GetAllTimeseriesForBenchmark(
          args.benchmark, args.days, args.filters):
        point = models.Timeseries.FromJson(point_data)
        db.Put(point)
