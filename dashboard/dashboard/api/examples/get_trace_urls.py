# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""An example of using perf dashboard API for getting list of traceUrls.

This example returns the traceURLs
required parameters:
  test_suite (e.g. "rendering.desktop")
  bot (e.g. "ChromiumPerf:Win 7 Nvidia GPU Perf")
  measurement (e.g. frame_times)
Optional parameter:
  to_date (specifying the end of timespan that we want the trace urls for)
  from_date (specifying the start of timespan that we want the trace urls for)
  output_traces (path for recording the list of trace urls)
  output_revs (path for recording the pairs of trace and revision number)
"""

import argparse
import csv
import datetime as dt
import json
import sys
import httplib2
from oauth2client import client

OAUTH_CLIENT_ID = (
    '62121018386-h08uiaftreu4dr3c4alh3l7mogskvb7i.apps.googleusercontent.com')
OAUTH_CLIENT_SECRET = 'vc1fZfV1cZC6mgDSHV-KSPOz'
SCOPES = ['https://www.googleapis.com/auth/userinfo.email']


def Main(argv):
  parser = argparse.ArgumentParser(
      description=('Returns the trace urls and coresponding revisions.'
                   'required parameters (bot and measurement) can be '
                   'found using "describe" api'))
  parser.add_argument('test_suite',
                      help='Name of test_suit (example: "rendering.desktop")')
  parser.add_argument('bot', help='Name of bot (example: "ChromiumPerf:Win 7 '
                      'Nvidia GPU Perf")')
  parser.add_argument('measurement', help='Name of measurement (example: '
                      '"frame_times")')
  parser.add_argument('--max_date', default=str(dt.datetime.now().date()),
                      type=str, help='The last date("YYYY-MM-DD") of timespan '
                      'that traces are needed for (default is today)')
  parser.add_argument('--min_date', default=
                      str((dt.datetime.now() - dt.timedelta(days=180)).date()),
                      type=str, help='The first date("YYYY-MM-DD") of timespan'
                      ' that traces are needed for (default is 6 months ago)')
  parser.add_argument('--output', default='/tmp/Urls_revisions.txt', type=str,
                      help='Path for output file')

  args = parser.parse_args(argv[1:])

  test_suite = args.test_suite.replace(' ', '+')
  bot = args.bot.replace(' ', '+')
  measurement = args.measurement.replace(' ', '+')
  min_timestamp = dt.datetime.strptime(args.min_date, '%Y-%m-%d').isoformat()
  max_timestamp = dt.datetime.strptime(args.max_date, '%Y-%m-%d').isoformat()

  response, content = MakeApiRequest(test_suite, bot, measurement,
                                     min_timestamp, max_timestamp)
  # Check response and do stuff with content!
  if response['status'] != '200':
    print response
    return

  json_data = json.loads(content)
  for elements in json_data['data']:
    (revision, histogram) = elements
    with open(args.output, 'a+') as output_file:
      csv_writer = csv.writer(output_file, delimiter=',')
      if histogram is not None and 'diagnostics' in histogram:
        if 'traceUrls' in histogram['diagnostics']:
          for url in histogram['diagnostics']['traceUrls']['values']:
            csv_writer.writerow([url, revision['r_commit_pos']])



def MakeApiRequest(test_suite, bot, measurement, min_timestamp, max_timestamp):
  flow = client.OAuth2WebServerFlow(
      OAUTH_CLIENT_ID,
      OAUTH_CLIENT_SECRET,
      SCOPES,
      approval_prompt='force')
  flow.redirect_uri = client.OOB_CALLBACK_URN
  authorize_url = flow.step1_get_authorize_url()
  print(
      'Go to the following link in your browser:\n\n'
      '    %s\n' % authorize_url)
  code = raw_input('Enter verification code: ').strip()
  try:
    creds = flow.step2_exchange(code)
  except client.FlowExchangeError as e:
    print 'Authentication has failed: %s' % e
    return None, None

  http_auth = creds.authorize(httplib2.Http())

  url = ('https://chromeperf.appspot.com/api/timeseries2?bot=%s&measurement=%s'
         '&test_suite=%s&min_timestamp=%s&max_timestamp=%s&columns=revisions,'
         'histogram') % (bot, measurement, test_suite, min_timestamp,
                         max_timestamp)

  resp, content = http_auth.request(
      url,
      method='POST',
  )
  return (resp, content)

if __name__ == '__main__':
  sys.exit(Main(sys.argv))
