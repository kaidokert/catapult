# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import pytz

from apache_beam.options.pipeline_options import PipelineOptions


class ExportOptions(PipelineOptions):

  @classmethod
  def _add_argparse_args(cls, parser):  # pylint: disable=invalid-name
    parser.add_value_provider_argument(
        '--end_time',
        help=('End of range to fetch in YYYYMMDDHHmm format.'),
        default='')
    parser.add_value_provider_argument(
        '--start_time',
        help='Start of range to fetch in YYYYMMDDHHmm format.',
        default='')
    parser.add_value_provider_argument(
        '--testing',
        help='Whether to run Pipeline for testing purposes. This disables uploading to GCS.',
        default='no',
    )
    parser.add_argument(
        '--repo_to_export',
        help='Specify only to export a specific repo (e.g. chromium, webrtc). If not specified, all repos are exported to their respective GCS Buckets.',
        default='all',
    )

  def GetTimeRangeProvider(self):
    """Return an object with .Get() method that returns (start, end) tuple."""
    return _TimeRangeProvider(self.start_time, self.end_time)


class _TimeRangeProvider:

  def __init__(self, start_time, end_time):
    self._start_time = start_time
    self._end_time = end_time

  def Get(self):
    return self._GetTimes()

  def __str__(self):
    return '_TimeRangeProvider({}, {})'.format(self._start_time, self._end_time)

  def _GetTimes(self):
    current = datetime.datetime.now()
    delta_min = current.minute % 10

    start_time = self._start_time.get()
    if start_time == '':
      # Round to the nearest 10 mins, 30 minutes in the past.
      # 30 minutes in the past to allow for new parent tests to be created. 
      start_time = (current - datetime.timedelta(minutes=30+delta_min)).strftime('%Y%m%d%H%M')
    
    end_time = self._end_time.get()
    if end_time == '':
      end_time = (current - datetime.timedelta(minutes=20+delta_min)).strftime('%Y%m%d%H%M')
    
    return (datetime.datetime.strptime(start_time,
                                      '%Y%m%d%H%M').replace(tzinfo=pytz.UTC),
            datetime.datetime.strptime(end_time,
                                      '%Y%m%d%H%M').replace(tzinfo=pytz.UTC))
