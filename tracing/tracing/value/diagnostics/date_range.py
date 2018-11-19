# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import datetime

from tracing.value.diagnostics import diagnostic


class DateRange(diagnostic.Diagnostic):
  __slots__ = '_range',

  def __init__(self, ms):
    from tracing.value import histogram
    super(DateRange, self).__init__()
    self._range = histogram.Range()
    self._range.AddValue(ms)

  def __eq__(self, other):
    if not isinstance(other, DateRange):
      return False
    return self._range == other._range

  def __hash__(self):
    return id(self)

  @property
  def min_date(self):
    return datetime.datetime.utcfromtimestamp(self._range.min / 1000)

  @property
  def max_date(self):
    return datetime.datetime.utcfromtimestamp(self._range.max / 1000)

  @property
  def min_timestamp(self):
    return self._range.min

  @property
  def max_timestamp(self):
    return self._range.max

  @property
  def duration_ms(self):
    return self._range.duration

  def __str__(self):
    min_date = self.min_date.isoformat().replace('T', ' ')[:19]
    if self.duration_ms == 0:
      return min_date
    max_date = self.max_date.isoformat().replace('T', ' ')[:19]
    return min_date + ' - ' + max_date

  def _AsDictInto(self, dct):
    dct['min'] = self._range.min
    if self.duration_ms == 0:
      return
    dct['max'] = self._range.max

  @staticmethod
  def FromDict(dct):
    dr = DateRange(dct['min'])
    if 'max' in dct:
      dr._range.AddValue(dct['max'])
    return dr

  def CanAddDiagnostic(self, other_diagnostic):
    return isinstance(other_diagnostic, DateRange)

  def AddDiagnostic(self, other_diagnostic):
    self._range.AddRange(other_diagnostic._range)

