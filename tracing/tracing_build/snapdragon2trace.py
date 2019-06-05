# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import csv
import json

from tracing_build.merge_traces import LoadTrace

def AddSnapdragonProfilerData(snapdragon_csv, chrome_trace, output):
  # Read and process the Chrome trace file.
  trace = LoadTrace(chrome_trace)
  if isinstance(trace, list):
    trace = {'traceEvents': trace}
  if 'metadata' in trace and 'clock-offset-since-epoch' in trace['metadata']:
    clock_offset = int(trace['metadata']['clock-offset-since-epoch'])
  else:
    print 'Need the clock offset to convert Snapdragon profiler data.'
    return
  max_pid = 0
  min_ts = None
  max_ts = 0
  for event in trace['traceEvents']:
    max_pid = max(event['pid'], max_pid)
    max_pid = max(event['tid'], max_pid)
    if event['ph'] != 'M':
      ts = event['ts']
      max_ts = max(ts, max_ts)
      if min_ts is None or min_ts > ts:
        min_ts = ts

  # Read the Snapdragon profiler data and add it to the trace dict.
  process_names = {}
  counter = 0
  with open(snapdragon_csv, 'r') as snapdragon_csv_file:
    reader = csv.DictReader(snapdragon_csv_file, delimiter=',')
    for row in reader:
      ts = int(row['TimestampRaw']) - clock_offset
      if ts < min_ts or ts > max_ts:
        continue
      counter += 1
      if row['Process'] not in process_names:
        pid = max_pid + 1
        max_pid += 1
        process_names[row['Process']] = pid
        trace['traceEvents'].append({
            'pid': pid,
            'tid': pid,
            'ts': 0,
            'ph': 'M',
            'cat': '__metadata',
            'name': 'process_sort_index',
            'args': {'sort_index': -7}})
        trace['traceEvents'].append({
            'pid': pid,
            'tid': pid,
            'ts': 0,
            'ph': 'M',
            'cat': '__metadata',
            'name': 'process_name',
            'args': {'name': row['Process']}})
      else:
        pid = process_names[row['Process']]
        trace['traceEvents'].append({
            'pid': pid,
            'tid': pid,
            'ts': ts,
            'ph': 'C',
            'name': row['Metric'],
            'args': {'Value': float(row['Value'])}})
  print 'Added %d events.' % counter

  # Write the trace dict as a JSON.
  with open(output, 'w') as output_file:
    json.dump(trace, output_file)
