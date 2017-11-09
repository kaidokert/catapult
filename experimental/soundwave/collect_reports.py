#!/usr/bin/env python
# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import csv
import dashboard_api
import json
import os
import pandas as pd
import time


# pylint: disable=line-too-long
HELP_SITE = 'https://developers.google.com/api-client-library/python/auth/service-accounts#creatinganaccount'

_BASE_CONFIG = {
    'benchmark_noise_visualizer': True,
    'disabled_stories': None,
    'reports': {

    }
}


def FilterMetric(df, metric):
  m, s = metric.split('/', 1)
  temp = df[df['metric'] == m]
  return temp[temp['story'] == s]


def BisectOutcome(alert):
  return alert['bisect_status']


def BugOutcome(alert, bugs):
  bug_id = alert['bug_id']
  # No bug.
  if not bug_id:
    return 'NoBug'

  state = bugs[str(bug_id)]['state']
  status = bugs[str(bug_id)]['status']

  if bug_id == -1:
    return 'Invalid'
  if bug_id == -2:
    return 'Ignored'

  if state == 'open':
    if status == 'Untriaged':
      return status
    else:
      return 'Open'
  if status in ['WontFix', 'Duplicate']:
    return status
  if status in ['Fixed', 'Verified']:
    return 'Fixed'
  raise TypeError('Unknown bug outcome')


def GetBugData(dashboard_communicator, bug):
  """Returns data for given bug."""
  if not bug:
    return {'bug': {'state': None, 'status': None, 'summary': None}}
  if int(bug) == -1:
    return {'bug': {'state': None, 'status': None, 'summary': 'Invalid'}}
  if int(bug) == -2:
    return {'bug': {'state': None, 'status': None, 'summary': 'Ignored'}}
  data = dashboard_communicator.GetBugData(bug)
  # Only care about date of comments, not content.
  data['bug']['comments'] = [a['published'] for a in data['bug']['comments']]
  return data


def GenerateAlertData(credentials, days, benchmark, save_path):
  if os.path.exists(save_path):
    print 'Alert data already found. Skipping.'
    return
  data = []
  alerts = credentials.GetAlertData(benchmark, days)['anomalies']
  print '%s alerts found for benchmark %s!' % (len(alerts), benchmark)
  bug_list = set([a.get('bug_id') for a in alerts])
  print 'Collecting data for %d bugs.' % len(bug_list)
  bugs = {}
  for bug in bug_list:
    bugs[bug] = GetBugData(credentials, bug)['bug']

  data = {'bugs': bugs, 'alerts': alerts}
  with open(save_path, 'w') as fp:
    print 'Saving data to %s.' % save_path
    json.dump(data, fp, sort_keys=True, indent=2)
  return data


def GenerateTimeseriesData(credentials, days, benchmark, save_path):
  if os.path.exists(save_path):
    print 'Timeseries data already found. Skipping.'
    return True
  with open(save_path, 'wb') as fp:
    csv_writer = csv.writer(fp)
    data_written = False
    for row in credentials.GetAllTimeseriesForBenchmark(
        benchmark, days, None):
      csv_writer.writerow(row)
      data_written = True
  return data_written


def GenerateNoiseData(timeseries_path, alerts_path, save_path):
  if os.path.exists(save_path):
    print 'Noise data already found. Skipping.'
    return
  with open(alerts_path) as fp:
    alerts_raw = json.loads(fp.read())
  bugs = alerts_raw['bugs']
  alerts_json = alerts_raw['alerts']
  alerts = {}
  for alert in alerts_json:
    bot_ = alert['bot']
    test_ = alert['test']
    name = '%s:%s' % (bot_, test_)
    if not alerts.get(name):
      alerts[name] = []
    alerts[name].append(alert)

  with open(timeseries_path) as fp:
    df = pd.read_csv(fp, parse_dates=['timestamp'])

  metric_list = (df['metric'] + '/' + df['story']).unique()
  bot_list = df['bot'].unique()

  data = []
  for bot in bot_list:
    bot_filtered_df = df[df['bot'] == bot]
    for metric in metric_list:
      if metric.endswith('ref'):
        continue
      filtered_df = FilterMetric(bot_filtered_df, metric)
      ref_filtered_df = FilterMetric(bot_filtered_df, metric + '_ref')
      c = filtered_df.value.std() / filtered_df.value.mean() * 100
      ref_c = ref_filtered_df.value.std() / ref_filtered_df.value.mean() * 100

      alerts_dict = alerts.get('%s:%s' % (bot, metric), None)
      std = filtered_df.value.std()
      ref_std = ref_filtered_df.value.std()

      # Get alert data
      bisect_outcomes = []
      bug_outcomes = []

      if alerts_dict:
        bisect_outcomes = [BisectOutcome(a) for a in alerts_dict]
        bug_outcomes = [BugOutcome(a, bugs) for a in alerts_dict]
      num_alerts = len(alerts_dict) if alerts_dict else 0

      d = [
          bot, metric, c, ref_c, std, ref_std, num_alerts,
          len([x for x in bug_outcomes if x == 'Ignored']),
          len([x for x in bug_outcomes if x == 'Invalid']),
          len([x for x in bug_outcomes if x == 'NoBug']),
          (len([x for x in bug_outcomes if x == 'Open']) +
           len([x for x in bug_outcomes if x == 'Untriaged'])),
          len([x for x in bug_outcomes if x == 'Untriaged']),
          len([x for x in bug_outcomes if x == 'WontFix']),
          len([x for x in bug_outcomes if x == 'Fixed']),
          len([x for x in bug_outcomes if x == 'Duplicate']),
          len([x for x in bisect_outcomes if x == None]),
          len([x for x in bisect_outcomes if x == 'failed']),
          len([x for x in bisect_outcomes if x == 'completed'])
      ]
      data.append(d)

  headers = ['bot', 'metric', 'cv', 'ref_cv', 'std', 'ref_std', 'Alerts',
             'Ignored', 'Invalid', 'NoBug', 'OpenBug', 'UntriagedBug',
             'WontFixBug', 'FixedBug', 'Duplicate', 'NoBisect', 'FailedBisect',
             'SuccessfulBisect']
  r_df = pd.DataFrame(data, columns=headers)
  r_df.to_csv(save_path)


def GenerateReport(credentials, benchmark, days, config_to_update, output_path):
  alerts = output_path + '/' + benchmark + '.alerts'
  timeseries = output_path + '/' + benchmark + '.timeseries'
  noise = output_path + '/' + benchmark + '.noise'

  if GenerateTimeseriesData(credentials, days, benchmark, timeseries):
    GenerateAlertData(credentials, days, benchmark, alerts)
    GenerateNoiseData(timeseries, alerts, noise)
    config_to_update['reports'][benchmark] = {
        'alerts': alerts,
        'timeseries': timeseries,
        'noise': noise,
        'date': time.strftime('%D %H:%M:%S'),
        'duration': days
    }
  else:
    print (
        'Cannot generate noise data for %s. No timeseries data found. Leaving '
        'out of binder.' % benchmark)
    for f in [alerts, timeseries, noise]:
      if os.path.exists(f):
        os.remove(f)


def Main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-b', '--benchmark', required=True, action='append',
                      help='Benchmark to pull data for.')
  parser.add_argument('-d', '--days', default=30, type=int,
                      help='Number of days to collect data for. Default 30')
  parser.add_argument('-o', '--output-path', required=True,
                      help='Directory to save data to.')
  parser.add_argument('--credentials',
                      help=('Path to json credentials file. See %s for '
                            'information about generating this.' % HELP_SITE))
  parser.add_argument('--sheriff', help='Sheriff rotation alerts trigger for.')
  args = parser.parse_args()

  binder_path = args.output_path + '/binder.json'

  if not os.path.exists(args.output_path):
    os.makedirs(args.output_path)
  if not os.path.exists(binder_path):
    config = _BASE_CONFIG.copy()

  else:
    with open(binder_path) as f:
      try:
        config = json.load(f)
      except ValueError:
        print 'Config could not be decoded. Starting new one.'
        config = _BASE_CONFIG.copy()

  dashboard_communicator = dashboard_api.PerfDashboardCommunicator(
      json_key_path=args.credentials)

  for benchmark in args.benchmark:
    if config['reports'].get(benchmark):
      print ('Skipping benchmark %s as it is already in the binder. Delete '
             'from binder json to recollect.' % benchmark)
      continue
    GenerateReport(dashboard_communicator, benchmark, args.days, config,
                   args.output_path)
    with open(binder_path, 'w') as f:
      json.dump(config, f, sort_keys=True, indent=2)


if __name__ == '__main__':
  Main()
