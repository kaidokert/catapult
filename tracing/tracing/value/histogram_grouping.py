# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from tracing.value.diagnostics import reserved_infos


BY_KEY = {}


class HistogramGrouping(object):

  def __init__(self, key, callback):
    self._key = key
    self._callback = callback
    BY_KEY[key] = self

  @property
  def key(self):
    return self._key

  @property
  def callback(self):
    return self._callback

def BuildFromTags(tags, diagnostic_name):
  boolean_tags = set()
  key_value_tags = set()
  for tag in tags:
    if ':' in tag:
      key = tag.split(':')[0]
      assert key not in boolean_tags, key
      key_value_tags.add(key)
    else:
      assert tag not in key_value_tags, tag
      boolean_tags.add(tag)
  groupings = [
      _BuildBooleanTagGrouping(tag, diagnostic_name) for tag in boolean_tags]
  groupings += [
      _BuildKeyValueTagGrouping(key, diagnostic_name) for key in key_value_tags]
  return groupings


def _BuildBooleanTagGrouping(tag, diagnostic_name):
  def Closure(hist):
    tags = hist.diagnostics.get(diagnostic_name)
    if not tags or tag not in tags:
      return '~' + tag
    return tag
  return HistogramGrouping(tag + 'Tag', Closure)


def _BuildKeyValueTagGrouping(key, diagnostic_name):
  def Closure(hist):
    tags = hist.diagnostics.get(diagnostic_name)
    if not tags:
      return '~' + key
    values = set()
    for tag in tags:
      kvp = tag.split(':')
      if len(kvp) < 2 or kvp[0] != key:
        continue
      values.add(kvp[1])
    if len(values) == 0:
      return '~' + key
    return ','.join(sorted(values))
  return HistogramGrouping(key + 'Tag', Closure)


HISTOGRAM_NAME = HistogramGrouping('name', lambda h: h.name)


def _DisplayLabel(hist):
  labels = hist.diagnostics.get(reserved_infos.LABELS.name)
  if labels and len(labels):
    return ','.join(sorted(labels))

  benchmarks = hist.diagnostics.get(reserved_infos.BENCHMARKS.name)
  start = hist.diagnostics.get(reserved_infos.BENCHMARK_START.name)
  if not benchmarks:
    if not start:
      return 'Value'
    return start.ToString()
  benchmarks = '\n'.join(benchmarks)
  if not start:
    return benchmarks
  return benchmarks + '\n' + start.ToString()


DISPLAY_LABEL = HistogramGrouping('displayLabel', _DisplayLabel)


class GenericSetGrouping(HistogramGrouping):

  def __init__(self, name):
    super(GenericSetGrouping, self).__init__(name, self._Compute)

  def _Compute(self, hist):
    diag = hist.diagnostics.get(self.key)
    if not diag:
      return ''
    return ','.join(sorted(diag))


GenericSetGrouping(reserved_infos.ARCHITECTURES.name)
GenericSetGrouping(reserved_infos.BENCHMARKS.name)
GenericSetGrouping(reserved_infos.BOTS.name)
GenericSetGrouping(reserved_infos.BUILDS.name)
GenericSetGrouping(reserved_infos.DEVICE_IDS.name)
GenericSetGrouping(reserved_infos.MASTERS.name)
GenericSetGrouping(reserved_infos.MEMORY_AMOUNTS.name)
GenericSetGrouping(reserved_infos.OS_NAMES.name)
GenericSetGrouping(reserved_infos.OS_VERSIONS.name)
GenericSetGrouping(reserved_infos.PRODUCT_VERSIONS.name)
GenericSetGrouping(reserved_infos.STORIES.name)
GenericSetGrouping(reserved_infos.STORYSET_REPEATS.name)
GenericSetGrouping(reserved_infos.STORY_TAGS.name)


class DateRangeGrouping(HistogramGrouping):

  def __init__(self, name):
    super(DateRangeGrouping, self).__init__(name, self._Compute)

  def _Compute(self, hist):
    diag = hist.diagnostics.get(self.key)
    if not diag:
      return ''
    return diag.ToString()


DateRangeGrouping(reserved_infos.BENCHMARK_START.name)
DateRangeGrouping(reserved_infos.TRACE_START.name)
