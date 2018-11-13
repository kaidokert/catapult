# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime

import pandas  # pylint: disable=import-error


def EmptyFrame(column_types):
  """Create an empty DataFrame with the given column types."""
  df = pandas.DataFrame()
  for column, dtype in column_types:
    df[column] = pandas.Series(dtype=dtype)
  return df
