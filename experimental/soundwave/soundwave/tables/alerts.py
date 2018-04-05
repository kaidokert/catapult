# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import pandas  # pylint: disable=import-error


COLUMNS = (
    'key', 'timestamp', 'test_suite', 'measurement', 'bot', 'test_case',
    'start_revision', 'end_revision',
    'median_before_anomaly', 'median_after_anomaly', 'units', 'improvement',
    'bug_id', 'status', 'bisect_status')
INDEX = COLUMNS[0]


_CODE_TO_STATUS = {
    -2: 'ignored',
    -1: 'invalid',
    None: 'untriaged',
    # Any positive integer represents a bug_id and maps to a 'triaged' status.
}


def RowFromJson(data):
  """Turn json data from an alert into a tuple with values for that record."""
  data = data.copy()  # Do not modify the original dict.

  # Name fields using newer dashboard nomenclature.
  data['test_suite'] = data.pop('testsuite')
  data['measurement'], data['test_case'] = data.pop('test').split('/', 1)
  data['bot'] = '/'.join([data.pop('master'), data.pop('bot')])

  # Separate bug_id from alert status.
  data['status'] = _CODE_TO_STATUS.get(data['bug_id'], 'triaged')
  if data['status'] == 'triaged':
    assert data['bug_id'] > 0
  else:
    data['bug_id'] = None

  return tuple(data[k] for k in COLUMNS)


def DataFrameFromJson(data):
  df = pandas.DataFrame.from_records(
      (RowFromJson(d) for d in data['anomalies']), index=INDEX, columns=COLUMNS)
  df['timestamp'] = pandas.to_datetime(df['timestamp'])
  return df
