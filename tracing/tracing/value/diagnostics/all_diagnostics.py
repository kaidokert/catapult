# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import importlib
import sys


_MODULES_BY_DIAGNOSTIC_NAME = {
    'Breakdown': 'breakdown',
    'GenericSet': 'generic_set',
    'UnmergeableDiagnosticSet': 'unmergeable_diagnostic_set',
    'RelatedEventSet': 'related_event_set',
    'DateRange': 'date_range',
    'TagMap': 'tag_map',
    'RelatedHistogramBreakdown': 'related_histogram_breakdown',
    'RelatedHistogramMap': 'related_histogram_map',
    'RelatedNameMap': 'related_name_map',
}


_CLASSES_BY_NAME = {}


def IsDiagnosticTypename(name):
  return name in _MODULES_BY_DIAGNOSTIC_NAME


def GetDiagnosticTypenames():
  return _MODULES_BY_DIAGNOSTIC_NAME.keys()


def GetDiagnosticClassForName(name):
  assert IsDiagnosticTypename(name)

  if name in _CLASSES_BY_NAME:
    return _CLASSES_BY_NAME[name]

  module_name = ('tracing.value.diagnostics.%s'
                 % _MODULES_BY_DIAGNOSTIC_NAME[name])
  importlib.import_module(module_name)

  cls = getattr(sys.modules[module_name], name)
  _CLASSES_BY_NAME[name] = cls
  return cls
