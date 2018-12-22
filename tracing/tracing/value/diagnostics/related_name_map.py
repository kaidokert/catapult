# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from tracing.value.diagnostics import diagnostic


class RelatedNameMap(diagnostic.Diagnostic):
  __slots__ = '_map',

  def __init__(self):
    super(RelatedNameMap, self).__init__()
    self._map = {}

  def __eq__(self, other):
    if not isinstance(other, RelatedNameMap):
      return False
    if set(self._map) != set(other._map):
      return False
    for key, name in self._map.items():
      if name != other.Get(key):
        return False
    return True

  def __hash__(self):
    return id(self)

  def CanAddDiagnostic(self, other):
    return isinstance(other, RelatedNameMap)

  def AddDiagnostic(self, other):
    for key, name in other._map.items():
      existing = self.Get(key)
      if existing is None:
        self.Set(key, name)
      elif existing != name:
        raise ValueError('Histogram names differ: "%s" != "%s"' % (
            existing, name))

  def Get(self, key):
    return self._map.get(key)

  def Set(self, key, name):
    self._map[key] = name

  def __iter__(self):
    for key, name in self._map.items():
      yield key, name

  def Values(self):
    return self._map.values()

  def AsDict(self, serializer):
    return {key: serializer.GetNameId(name) for key, name in self}

  @staticmethod
  def FromDict(dct, deserializer=None):
    names = RelatedNameMap()
    if deserializer:
      for key, i in dct.items():
        names.Set(key, deserializer.GetNameById(i))
    else:
      for key, name in dct['names'].items():
        names.Set(key, name)
    return names
