# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

try:
  from py_utils import slots_metaclass
  SlotsMetaclass = slots_metaclass.SlotsMetaclass # pylint: disable=invalid-name
except ImportError:
  # TODO(benjhayden): Figure out why py_utils doesn't work in dev_appserver.py
  SlotsMetaclass = None # pylint: disable=invalid-name

from tracing.value.diagnostics import all_diagnostics


class Diagnostic(object):
  __slots__ = tuple()

  # Ensure that new subclasses remember to specify __slots__ in order to prevent
  # regressing memory consumption:
  if SlotsMetaclass:
    __metaclass__ = SlotsMetaclass

  def __ne__(self, other):
    return not self == other

  @staticmethod
  def FromDict(dct, unused_deserializer=None):
    cls = all_diagnostics.GetDiagnosticClassForName(dct['type'])
    if not cls:
      raise ValueError('Unrecognized diagnostic type: ' + dct['type'])
    diagnostic = cls.FromDict(dct)
    return diagnostic

  def CanAddDiagnostic(self, unused_other_diagnostic):
    return False

  def AddDiagnostic(self, unused_other_diagnostic):
    raise Exception('Abstract virtual method: subclasses must override '
                    'this method if they override canAddDiagnostic')

def FromDict(type_name, dct, deserializer):
  cls = all_diagnostics.GetDiagnosticClassForName(type_name)
  if not cls:
    raise ValueError('Unrecognized diagnostic type: ' + type_name)
  return cls.FromDict(dct, deserializer)
