# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import re

from typ.json_results import ResultType


_EXPECTATION_MAP = {
  'Crash': ResultType.Crash,
  'Failure': ResultType.Failure,
  'Pass': ResultType.Pass,
  'Timeout': ResultType.Timeout,
  'Skip': ResultType.Skip
}

class ParseError(Exception):
  pass


class Expectation(object):
  def __init__(self, reason, test, conditions, results):
    """Constructor for expectations.

    Args:
      reason: String that indicates the reason for disabling.
      test: String indicating which test is being disabled.
      conditions: List of tags indicating which conditions to disable for.
          Conditions are combined using logical and. Example: ['Mac', 'Debug']
      results: List of outcomes for test. Example: ['Skip', 'Pass']
    """
    assert isinstance(reason, basestring) or reason is None
    self._reason = reason
    assert isinstance(test, basestring)
    self._test = test
    assert isinstance(conditions, list)
    self._conditions = conditions
    assert isinstance(results, list)
    self._results = results

  def __eq__(self, other):
    return (self.reason == other.reason and
            self.test == other.test and
            self.conditions == other.conditions and
            self.results == other.results)

  @property
  def reason(self):
    return self._reason

  @property
  def test(self):
    return self._test

  @property
  def conditions(self):
    return self._conditions

  @property
  def results(self):
    return self._results


class TestExpectationParser(object):
  """Parses lists of tests and expectations for them.

  This parser covers the 'tagged' test lists format in:
      bit.ly/chromium-test-list-format

  Takes raw expectations data as a string read from the TA/DA expectation file
  in the format:

    # This is an example expectation file.
    #
    # tags: [
    #   Mac Mac10.1 Mac10.2
    #   Win Win8
    # ]
    # tags: [ Release Debug ]

    crbug.com/123 [ Win ] benchmark/story [ Skip ]
    ...
  """

  TAG_TOKEN = '# tags: ['
  _MATCH_STRING = r'^(?:(crbug.com/\d+) )?'  # The bug field (optional).
  _MATCH_STRING += r'(?:\[ (.+) \] )?' # The label field (optional).
  _MATCH_STRING += r'(\S+) ' # The test path field.
  _MATCH_STRING += r'\[ ([^\[.]+) \]'  # The expectation field.
  _MATCH_STRING += r'(\s+#.*)?$' # End comment (optional).
  MATCHER = re.compile(_MATCH_STRING)

  def __init__(self, raw_data):
    self.tag_sets = []
    self.expectations = []
    self._ParseRawExpectationData(raw_data)

  def _ParseRawExpectationData(self, raw_data):
    lines = raw_data.splitlines()
    line_number = 1
    num_lines = len(lines)
    while line_number <= num_lines:
      line = lines[line_number - 1].strip()
      if line.startswith(self.TAG_TOKEN):
        # Handle tags.
        if self.expectations:
          raise ParseError('Tag found after first expectation.')
        right_bracket = line.find(']')
        if right_bracket == -1:
          # multi-line tag set
          tag_set = set(line[len(self.TAG_TOKEN):].split())
          line_number += 1
          while line_number <= num_lines and right_bracket == -1:
            line = lines[line_number - 1].strip()
            if line[0] != '#':
              raise ParseError('Multi-line tag set missing leading "#"')
            right_bracket = line.find(']')
            if right_bracket == -1:
              tag_set.update(line[1:].split())
            else:
              tag_set.update(line[1:right_bracket].split())
            line_number += 1
        else:
          tag_set = set(line[len(self.TAG_TOKEN):right_bracket].split())
        self.tag_sets.append(tag_set)
      elif line.startswith('#') or not line:
        # Ignore, it is just a comment or empty.
        line_number += 1
        continue
      else:
        self.expectations.append(
            self._ParseExpectationLine(line_number, line, self.tag_sets))
      line_number += 1

  def _ParseExpectationLine(self, line_number, line, tag_sets):
    match = self.MATCHER.match(line)
    if not match:
      raise ParseError(
          'Expectation has invalid syntax on line %d: %s'
          % (line_number, line))
    # Unused group is optional trailing comment.
    reason, raw_conditions, test, raw_results, _ = match.groups()
    conditions = [c for c in raw_conditions.split()] if raw_conditions else []

    for c in conditions:
      if not any (c in tag_set for tag_set in tag_sets):
        raise ParseError(
            'Condition %s not found in expectations tag data. Line %d'
            % (c, line_number))

    results = []
    for r in raw_results.split():
      try:
        results.append(_EXPECTATION_MAP[r])
      except KeyError:
        raise ParseError(
            'Unknown result type %s on line %d' % (r, line_number))
    
    return Expectation(reason, test, conditions, results)
