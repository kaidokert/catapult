# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from . import histogram_serializer


class HistogramDeserializer(object):
  def __init__(self, dct):
    self._names = dct[histogram_serializer.NAMES_TAG]
