# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections

from soundwave import utils


_Timeseries = collections.namedtuple('Timeseries', [
    'test_path', 'point_id', 'value', 'timestamp',
    'commit_pos', 'chromium_rev', 'clank_rev'])


class Timeseries(_Timeseries):
  __slots__ = ()
  name = 'timeseries'
  columns = _Timeseries._fields

  @classmethod
  def FromTuple(cls, row):
    return cls._make(row)

  @classmethod
  def FromJson(cls, data):
    return cls(
        test_path=data['test_path'],
        point_id=data['revision'],
        value=data['value'],
        timestamp=utils.IsoFormatStrToTimestamp(data['timestamp']),
        commit_pos=int(data['r_commit_pos']),
        chromium_rev=data['r_chromium'],
        clank_rev=data.get('r_clank', None)
    )
