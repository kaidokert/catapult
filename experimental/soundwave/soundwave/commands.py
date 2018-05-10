# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import division

import multiprocessing
import pandas  # pylint: disable=import-error
import sqlite3
import sys

from soundwave import dashboard_api
from soundwave import pandas_sqlite
from soundwave import tables


def FetchAlertsData(args):
  api = dashboard_api.PerfDashboardCommunicator(args)
  con = sqlite3.connect(args.database_file)
  try:
    alerts = tables.alerts.DataFrameFromJson(
        api.GetAlertData(args.benchmark, args.days))
    print '%d alerts found!' % len(alerts)
    pandas_sqlite.InsertOrReplaceRecords(alerts, 'alerts', con)

    bug_ids = set(alerts['bug_id'].unique())
    bug_ids.discard(0)  # A bug_id of 0 means untriaged.
    print '%d bugs found!' % len(bug_ids)
    if args.use_cache and tables.bugs.HasTable(con):
      known_bugs = set(
          b for b in bug_ids if tables.bugs.Get(con, b) is not None)
      if known_bugs:
        print '(skipping %d bugs already in the database)' % len(known_bugs)
        bug_ids.difference_update(known_bugs)
    bugs = tables.bugs.DataFrameFromJson(api.GetBugData(bug_ids))
    pandas_sqlite.InsertOrReplaceRecords(bugs, 'bugs', con)
  finally:
    con.close()


def _SkipTestPathsInCache(con, test_paths):
  """Iterate over test_paths skipping over those with recent data in the db."""
  a_day_ago = pandas.Timestamp.utcnow() - pandas.Timedelta(days=1)
  a_day_ago = a_day_ago.tz_convert(tz=None)

  for test_path in test_paths:
    latest = tables.timeseries.GetMostRecentPoint(con, test_path)
    if latest is None or latest['timestamp'] < a_day_ago:
      yield test_path


def _TimeseriesWorker(test_path):
  try:
    api = _TimeseriesWorker.api
    con = _TimeseriesWorker.con
    data = api.GetTimeseries(test_path, days=_TimeseriesWorker.days)
    timeseries = tables.timeseries.DataFrameFromJson(data)
    pandas_sqlite.InsertOrReplaceRecords(timeseries, 'timeseries', con)
  except KeyboardInterrupt:
    pass


def _InitTimeseriesWorker(args):
  _TimeseriesWorker.days = args.days
  _TimeseriesWorker.api = api = dashboard_api.PerfDashboardCommunicator(args)
  _TimeseriesWorker.con = sqlite3.connect(args.database_file)


def FetchTimeseriesData(args):
  def _MatchesAllFilters(test_path):
    return all(f in test_path for f in args.filters)

  api = dashboard_api.PerfDashboardCommunicator(args)
  con = sqlite3.connect(args.database_file)
  try:
    test_paths = api.ListTestPaths(args.benchmark, sheriff=args.sheriff)
    if args.filters:
      test_paths = filter(_MatchesAllFilters, test_paths)
    num_found = len(test_paths)
    print '%d test paths found!' % num_found

    if args.use_cache and tables.timeseries.HasTable(con):
      test_paths = list(_SkipTestPathsInCache(con, test_paths))
      num_found, prev_num_found = len(test_paths), num_found
      num_skipped = prev_num_found - num_found
      if num_skipped:
        print '(skipping %d test paths already in the database)' % num_skipped
  finally:
    con.close()

  test_paths = test_paths[:100]
  num_found = len(test_paths)

  time_started = pandas.Timestamp.utcnow()
  sys.stdout.write('Fetching %d timeseries: ' % num_found)
  sys.stdout.flush()
  pool = multiprocessing.Pool(
      processes=10, initializer=_InitTimeseriesWorker, initargs=(args, ))
  for _ in pool.imap_unordered(_TimeseriesWorker, test_paths):
    sys.stdout.write('.')
    sys.stdout.flush()
  sys.stdout.write('\n')
  time_finished = pandas.Timestamp.utcnow()
  test_paths_per_sec = num_found / (time_finished - time_started).seconds
  print '[Speed: %.1f test paths per second]' % test_paths_per_sec
