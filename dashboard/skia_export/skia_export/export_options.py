# Copyright (c) 2020 The Chromium Authors. All rights reserved.
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
        help=(
            'End of range to fetch in YYYYMMDDHH format.'),
        default='')
    parser.add_value_provider_argument(
        '--start_time',
        help='Start of range to fetch in YYYYMMDDHH format.',
        default='')

  def GetTimeRangeProvider(self):
    """Return an object with .Get() method that returns (start, end) tuple."""
    return _TimeRangeProvider(self.start_time, self.end_time)


class _TimeRangeProvider:

  def __init__(self, start_time, end_time):
    self._start_time = start_time
    self._end_time = end_time

  def Get(self):
    return (self._StartTime(), self._EndTime())

  def __str__(self):
    return '_TimeRangeProvider({}, {})'.format(self._start_time, self._end_time)

  def _StartTime(self):
    start_time = self._start_time.get()
    if start_time == '':
      start_time = (datetime.datetime.utcnow() -
                    datetime.timedelta(hours=1)).strftime('%Y%m%d%H')
    return datetime.datetime.strptime(start_time,
                                      '%Y%m%d%H').replace(tzinfo=pytz.UTC)

  def _EndTime(self):
    end_time = self._end_time.get()
    if end_time == '':
      end_time = (datetime.datetime.utcnow().strftime('%Y%m%d%H'))
    return datetime.datetime.strptime(end_time,
                                      '%Y%m%d%H').replace(tzinfo=pytz.UTC)
