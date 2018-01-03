# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import importlib
import sys


MODULES_BY_DIAGNOSTIC_NAME = {
    'Breakdown': 'histogram',
    'GenericSet': 'histogram',
    'UnmergeableDiagnosticSet': 'histogram',
    'RelatedEventSet': 'histogram',
    'DateRange': 'histogram',
    'TagMap': 'histogram',
    'RelatedHistogramBreakdown': 'histogram',
    'RelatedHistogramMap': 'histogram',
    'RelatedNameMap': 'histogram',
}


_CLASSES_BY_NAME = {}


def GetDiagnosticClassForName(name):
  if name in _CLASSES_BY_NAME:
    return _CLASSES_BY_NAME[name]

  module_name = 'tracing.value.%s' % MODULES_BY_DIAGNOSTIC_NAME[name]
  importlib.import_module(module_name)

  cls = getattr(sys.modules[module_name], name)
  _CLASSES_BY_NAME[name] = cls
  return cls
