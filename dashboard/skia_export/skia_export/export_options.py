# Copyright (c) 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import pytz

from apache_beam.options.pipeline_options import PipelineOptions


def _YesterdayUTC():
  return (datetime.datetime.utcnow() -
          datetime.timedelta(hours=1)).strftime('%Y%m%d%H')


class ExportOptions(PipelineOptions):

  @classmethod
  def _add_argparse_args(cls, parser):  # pylint: disable=invalid-name
    parser.add_value_provider_argument(
        '--end_time',
        help=(
            'Last hour of data to export in YYYYMMDDHH format, or special value '
            '"last_hour".  Default is last_hour.  Timezone is always UTC.'),
        default="last_hour")
    parser.add_value_provider_argument(
        '--num_hours',
        help='Number of hours data to export',
        type=int,
        default=1)

  def GetTimeRangeProvider(self):
    """Return an object with .Get() method that returns (start, end) tuple.

    In other words, returns the time range specified by --end_time and
    --num_hours as a pair of datetime.datetime objects.
    """
    return _TimeRangeProvider(self.end_time, self.num_hours)


class _TimeRangeProvider:
  """A ValueProvider-like based on the end_time and num_hours ValueProviders.

  This class is a workaround for the lack of NestedValueProviders in Beam's
  Python SDK.
  """

  def __init__(self, end_time, num_hours):
    self._end_time = end_time
    self._num_hours = num_hours

  def Get(self):
    return (self._StartTime(), self._EndTime())

  def __str__(self):
    return '_TimeRangeProvider({}, {})'.format(self._end_time, self._num_hours)

  def _EndAsDatetime(self):
    # pylint: disable=access-member-before-definition
    end_time = self._end_time.get()
    if end_time == 'last_hour':
      end_time = _YesterdayUTC()
    return datetime.datetime.strptime(end_time,
                                      '%Y%m%d%H').replace(tzinfo=pytz.UTC)

  def _StartTime(self):
    # pylint: disable=access-member-before-definition
    return self._EndTime() - datetime.timedelta(hours=self._num_hours.get())

  def _EndTime(self):
    return self._EndAsDatetime()
