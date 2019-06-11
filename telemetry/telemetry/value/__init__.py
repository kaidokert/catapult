# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""
The Value hierarchy provides a way of representing the values measurements
produce such that they can be merged across runs, grouped by page, and output
to different targets.

The core Value concept provides the basic functionality:
- association with a page, may be none
- naming and units
- importance tracking [whether a value will show up on a waterfall or output
  file by default]
- other metadata, such as a description of what was measured
- default conversion to scalar and string
- merging properties

A page may actually run a few times during a single telemetry session.
Downstream consumers of test results typically want to group these runs
together, then compute summary statistics across runs. Value provides the
Merge* family of methods for this kind of aggregation.
"""
import os

from telemetry.core import util

from py_utils import discover


class Value(object):
  """An abstract value produced by a telemetry page test.
  """
  def __init__(self, page, name, units, important, description,
               grouping_label):
    """A generic Value object.

    Args:
      page: A Page object, may be given as None to indicate that the value
          represents results for multiple pages.
      name: A value name string, may contain a dot. Values from the same test
          with the same prefix before the dot may be considered to belong to
          the same chart.
      units: A units string.
      important: Whether the value is "important". Causes the value to appear
          by default in downstream UIs.
      description: A string explaining in human-understandable terms what this
          value represents.
      grouping_label: A label used to group values when summarizing.
          Note: this used to be called 'tir_label', although that is now an
          obsolete concept.
    """
    # TODO(eakuefner): Check story here after migration (crbug.com/442036)
    if not isinstance(name, basestring):
      raise ValueError('name field of Value must be string.')
    if not isinstance(units, basestring):
      raise ValueError('units field of Value must be string.')
    if not isinstance(important, bool):
      raise ValueError('important field of Value must be bool.')
    if not ((description is None) or isinstance(description, basestring)):
      raise ValueError('description field of Value must absent or string.')
    if not ((grouping_label is None) or
            isinstance(grouping_label, basestring)):
      raise ValueError('grouping_label field of Value must absent or '
                       'string.')

    self.page = page
    self.name = name
    self.units = units
    self.important = important
    self.description = description
    self._grouping_label = grouping_label

  def __eq__(self, other):
    return hash(self) == hash(other)

  def __hash__(self):
    return hash(str(self))

  def IsMergableWith(self, that):
    # pylint: disable=unidiomatic-typecheck
    return (self.units == that.units and
            type(self) == type(that) and
            self.important == that.important)

  @classmethod
  def MergeLikeValuesFromSamePage(cls, values):
    """Combines the provided list of values into a single compound value.

    When a page runs multiple times, it may produce multiple values. This
    function is given the same-named values across the multiple runs, and has
    the responsibility of producing a single result.

    It must return a single Value. If merging does not make sense, the
    implementation must pick a representative value from one of the runs.

    For instance, it may be given
        [ScalarValue(page, 'a', 1), ScalarValue(page, 'a', 2)]
    and it might produce
        ListOfScalarValues(page, 'a', [1, 2])
    """
    raise NotImplementedError()

  @classmethod
  def MergeLikeValuesFromDifferentPages(cls, values):
    """Combines the provided values into a single compound value.

    When a full pageset runs, a single value_name will usually end up getting
    collected for multiple pages. For instance, we may end up with
       [ScalarValue(page1, 'a',  1),
        ScalarValue(page2, 'a',  2)]

    This function takes in the values of the same name, but across multiple
    pages, and produces a single summary result value. In this instance, it
    could produce a ScalarValue(None, 'a', 1.5) to indicate averaging, or even
    ListOfScalarValues(None, 'a', [1, 2]) if concatenated output was desired.

    Some results are so specific to a page that they make no sense when
    aggregated across pages. If merging values of this type across pages is
    non-sensical, this method may return None.
    """
    raise NotImplementedError()

  @property
  def name_suffix(self):
    """Returns the string after a . in the name, or the full name otherwise."""
    if '.' in self.name:
      return self.name.split('.', 1)[1]
    else:
      return self.name

  @staticmethod
  def GetJSONTypeName():
    """Gets the typename for serialization to JSON using AsDict."""
    raise NotImplementedError()

  @property
  def grouping_label(self):
    return self._grouping_label

  def SetGroupingLabel(self, value):
    assert value, 'Should not set an empty grouping label'
    if self._grouping_label is not None and self._grouping_label != value:
      raise ValueError(
          'Value already has a grouping_label (%s) that does not match the '
          'supplied one (%s)' % (self._grouping_label, value))
    else:
      self._grouping_label = value

  def AsDict(self):
    """Pre-serializes a value to a dict for output as JSON."""
    return self._AsDictImpl()

  def _AsDictImpl(self):
    d = {
        'name': self.name,
        'type': self.GetJSONTypeName(),
        'units': self.units,
        'important': self.important
    }

    if self.description:
      d['description'] = self.description

    if self.grouping_label:
      # Some clients might still depend on the legacy name 'tir_label'.
      d['tir_label'] = self.grouping_label

    if self.page:
      d['page_id'] = self.page.id

    return d


def MergedGroupingLabel(values):
  """Returns the grouping_label that should be applied to a merge of values.

  Args:
    values: a list of Value instances

  Returns:
    The grouping_label that would be set on the merge of |values|.
  """
  assert len(values) > 0
  v0 = values[0]

  first_label = v0.grouping_label
  if all(v.grouping_label == first_label for v in values):
    return first_label
  else:
    return None
