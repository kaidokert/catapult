# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import tempfile
import unittest

from telemetry.story import expectations_parser


class TestExpectationParserTest(unittest.TestCase):
  def setUp(self):
    self._cleanup_list = []

  def tearDown(self):
    for f in self._cleanup_list:
      if os.path.exists(f):
        os.remove(f)

  def writeData(self, data):
    with tempfile.NamedTemporaryFile(delete=False) as mf:
      mock_file = mf.name
      self._cleanup_list.append(mock_file)
      mf.write(data)
    return mock_file

  def testInitNoFile(self):
    with self.assertRaises(AssertionError):
      expectations_parser.TestExpectationParser('No Path')

  def testInitGoodData(self):
    good_data = """
# This is a test expectation file.
#
# tags: tag1 tag2 tag3
# tags: tag4 Mac Win Debug

crbug.com/12345 [ Mac ] b1/s1 [ Skip ]
crbug.com/23456 [ Mac Debug ] b1/s2 [ Skip ]
"""
    mock_file = self.writeData(good_data)
    parser = expectations_parser.TestExpectationParser(mock_file)
    tags = ['tag1', 'tag2', 'tag3', 'tag4', 'Mac', 'Win', 'Debug']
    self.assertEqual(parser.tags, tags)
    expected_outcome = [
        {
            'test': 'b1/s1',
            'conditions': ['Mac'],
            'reason': 'crbug.com/12345',
            'results': ['Skip']
        },
        {
            'test': 'b1/s2',
            'conditions': ['Mac', 'Debug'],
            'reason': 'crbug.com/23456',
            'results': ['Skip']
        }
    ]
    self.assertEqual(parser.expectations, expected_outcome)

  def testInitBadData(self):
    bad_data = """
# This is a test expectation file.
#
# tags: tag1 tag2 tag3
# tags: tag4

crbug.com/12345 [ Mac b1/s1 [ Skip ]
"""
    bad_file = self.writeData(bad_data)
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(bad_file)


  def testParseExpectationLineEverythingThere(self):
    e = expectations_parser.TestExpectationParser._ParseExpectationLine(
        'crbug.com/23456 [ Mac ] b1/s2 [ Skip ]', ['Mac'])
    expected_outcome = {
        'test': 'b1/s2', 'conditions': ['Mac'], 'reason': 'crbug.com/23456',
        'results': ['Skip']
    }
    self.assertEqual(e, expected_outcome)

  def testParseExpectationLineBadTag(self):
    with self.assertRaises(AssertionError):
      expectations_parser.TestExpectationParser._ParseExpectationLine(
          'crbug.com/23456 [ Mac ] b1/s2 [ Skip ]', ['None'])

  def testParseExpectationLineNoConditions(self):
    e = expectations_parser.TestExpectationParser._ParseExpectationLine(
        'crbug.com/12345 b1/s1 [ Skip ]', ['All'])
    expected_outcome = {
        'test': 'b1/s1', 'conditions': [], 'reason': 'crbug.com/12345',
        'results': ['Skip']
    }
    self.assertEqual(e, expected_outcome)

  def testParseExpectationLineNoBug(self):
    e = expectations_parser.TestExpectationParser._ParseExpectationLine(
        '[ All ] b1/s1 [ Skip ]', ['All'])
    expected_outcome = {
        'test': 'b1/s1', 'conditions': ['All'], 'reason': None,
        'results': ['Skip']
    }
    self.assertEqual(e, expected_outcome)

  def testParseExpectationLineNoBugNoConditions(self):
    e = expectations_parser.TestExpectationParser._ParseExpectationLine(
        'b1/s1 [ Skip ]', ['All'])
    expected_outcome = {
        'test': 'b1/s1', 'conditions': [], 'reason': None,
        'results': ['Skip']
    }
    self.assertEqual(e, expected_outcome)

  def testParseExpectationLineMultipleConditions(self):
    e = expectations_parser.TestExpectationParser._ParseExpectationLine(
        'crbug.com/123 [ All None Batman ] b1/s1 [ Skip ]',
        ['All', 'None', 'Batman'])
    expected_outcome = {
        'test': 'b1/s1', 'conditions': ['All', 'None', 'Batman'],
        'reason': 'crbug.com/123', 'results': ['Skip']
    }
    self.assertEqual(e, expected_outcome)

  def testParseExpectationLineBadConditionBracket(self):
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser._ParseExpectationLine(
          'crbug.com/23456 ] Mac ] b1/s2 [ Skip ]', ['Mac'])

  def testparseExpectationLineBadResultBracket(self):
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser._ParseExpectationLine(
          'crbug.com/23456 ] Mac ] b1/s2 ] Skip ]', ['Mac'])

  def testParseExpectationLineBadConditionBracketSpacing(self):
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser._ParseExpectationLine(
          'crbug.com/2345 [Mac] b1/s1 [ Skip ]', ['Mac'])

  def testParseExpectationLineBadResultBracketSpacing(self):
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser._ParseExpectationLine(
          'crbug.com/2345 [ Mac ] b1/s1 [Skip]', ['Mac'])

  def testParseExpectationLineNoClosingConditionBracket(self):
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser._ParseExpectationLine(
          'crbug.com/2345 [ Mac b1/s1 [ Skip ]', ['Mac'])

  def testParseExpectationLineNoClosingResultBracket(self):
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser._ParseExpectationLine(
          'crbug.com/2345 [ Mac ] b1/s1 [ Skip', ['Mac'])

