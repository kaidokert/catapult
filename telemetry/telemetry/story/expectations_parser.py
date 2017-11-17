# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import re


class ParseError(Exception):
  pass


class TestExpectationParser(object):
  """Parse expectations file.

  This parser covers the 'tagged' test lists format in:
      go/chromium-test-list-format.

  It takes the path to the expectation file as an argument.

  Example expectation file to parse:
    # This is an example expectation file.
    #
    # tags: Mac Mac10.10 Mac10.11
    # tags: Win Win8

    crbug.com/123 [ Win ] benchmark/story [ Skip ]
  """

  TAG_TOKEN = '# tags:'
  _MATCH_STRING = r'(?:(crbug.com/\d+) )?'  # The bug field (optional).
  _MATCH_STRING += r'(?:\[ (.+) \] )?' # The label field (optional).
  _MATCH_STRING += r'([\w/]+) '  # The test path field.
  _MATCH_STRING += r'\[ (.+) \]'  # The expectation field.
  MATCHER = re.compile(_MATCH_STRING)

  def __init__(self, path):
    assert os.path.exists(path), 'Path to expectation file must exist.'
    self._path = path
    self._tags = []
    self._expectations = []
    self._ParseExpectationFile(path)

  def _ParseExpectationFile(self, path):
    with open(path, 'r') as fp:
      raw_data = fp.read()

    for line in raw_data.splitlines():
      # Handle metadata and comments.
      if line.startswith(self.TAG_TOKEN):
        for word in line[len(self.TAG_TOKEN):].split():
          self._tags.append(word)
      elif line.startswith('#') or not line:
        continue  # Ignore, it is just a comment or empty.
      else:
        self._expectations.append(self._ParseExpectationLine(line, self._tags))

  @classmethod
  def _ParseExpectationLine(cls, line, tags):
    match = cls.MATCHER.match(line)
    if not match:
      raise ParseError('Error when parsing line: %s' % line)
    reason, raw_conditions, test, results = match.groups()
    conditions = [c for c in raw_conditions.split()] if raw_conditions else []

    for c in conditions:
      assert c in tags

    return {
        'reason': reason,
        'test': test,
        'conditions': conditions,
        'results': [r for r in results.split()]
    }

  @property
  def expectations(self):
    return self._expectations

  @property
  def tags(self):
    return self._tags
