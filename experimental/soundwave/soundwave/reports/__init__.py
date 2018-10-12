#!/usr/bin/env python
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from soundwave.reports import v8_report


_REPORTS = {'v8': v8_report}

NAMES = sorted(_REPORTS)


def IterTestPaths(report):
  return _REPORTS[report].IterTestPaths()
