# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


import unittest

from py_utils import expectations_parser


class TestExpectationParserTest(unittest.TestCase):

  def testInitWithPathNoFile(self):
    with self.assertRaises(ValueError):
      expectations_parser.TestExpectationParser(path='No Path')

  def testInitNoData(self):
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(path=None, raw=None)

  def testInitWithGoodData(self):
    good_data = """
# This is a test expectation file.
#
# tags: tag1 tag2 tag3
# tags: tag4 Mac Win Debug

crbug.com/12345 [ Mac ] b1/s1 [ Skip ]
crbug.com/23456 [ Mac Debug ] b1/s2 [ Skip ]
"""
    parser = expectations_parser.TestExpectationParser(raw=good_data)
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

  def testInitWithBadData(self):
    bad_data = """
# This is a test expectation file.
#
# tags: tag1 tag2 tag3
# tags: tag4

crbug.com/12345 [ Mac b1/s1 [ Skip ]
"""
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(raw=bad_data)

  def testTagAfterExpectationsStart(self):
    bad_data = """
# This is a test expectation file.
#
# tags: tag1 tag2 tag3

crbug.com/12345 [ tag1 ] b1/s1 [ Skip ]

# tags: tag4
"""
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(raw=bad_data)

  def testParseExpectationLineEverythingThere(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    e = parser._ParseExpectationLine(
        0, 'crbug.com/23456 [ Mac ] b1/s2 [ Skip ]', ['Mac'])
    expected_outcome = {
        'test': 'b1/s2', 'conditions': ['Mac'], 'reason': 'crbug.com/23456',
        'results': ['Skip']
    }
    self.assertEqual(e, expected_outcome)

  def testParseExpectationLineBadTag(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    with self.assertRaises(expectations_parser.ParseError):
      parser._ParseExpectationLine(
          0, 'crbug.com/23456 [ Mac ] b1/s2 [ Skip ]', ['None'])

  def testParseExpectationLineNoConditions(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    e = parser._ParseExpectationLine(
        0, 'crbug.com/12345 b1/s1 [ Skip ]', ['All'])
    expected_outcome = {
        'test': 'b1/s1', 'conditions': [], 'reason': 'crbug.com/12345',
        'results': ['Skip']
    }
    self.assertEqual(e, expected_outcome)

  def testParseExpectationLineNoBug(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    e = parser._ParseExpectationLine(0, '[ All ] b1/s1 [ Skip ]', ['All'])
    expected_outcome = {
        'test': 'b1/s1', 'conditions': ['All'], 'reason': None,
        'results': ['Skip']
    }
    self.assertEqual(e, expected_outcome)

  def testParseExpectationLineNoBugNoConditions(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    e = parser._ParseExpectationLine(0, 'b1/s1 [ Skip ]', ['All'])
    expected_outcome = {
        'test': 'b1/s1', 'conditions': [], 'reason': None,
        'results': ['Skip']
    }
    self.assertEqual(e, expected_outcome)

  def testParseExpectationLineMultipleConditions(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    e = parser._ParseExpectationLine(
        0, 'crbug.com/123 [ All None Batman ] b1/s1 [ Skip ]',
        ['All', 'None', 'Batman'])
    expected_outcome = {
        'test': 'b1/s1', 'conditions': ['All', 'None', 'Batman'],
        'reason': 'crbug.com/123', 'results': ['Skip']
    }
    self.assertEqual(e, expected_outcome)

  def testParseExpectationLineBadConditionBracket(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    with self.assertRaises(expectations_parser.ParseError):
      parser._ParseExpectationLine(
          0, 'crbug.com/23456 ] Mac ] b1/s2 [ Skip ]', ['Mac'])

  def testParseExpectationLineBadResultBracket(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    with self.assertRaises(expectations_parser.ParseError):
      parser._ParseExpectationLine(
          0, 'crbug.com/23456 ] Mac ] b1/s2 ] Skip ]', ['Mac'])

  def testParseExpectationLineBadConditionBracketSpacing(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    with self.assertRaises(expectations_parser.ParseError):
      parser._ParseExpectationLine(
          0, 'crbug.com/2345 [Mac] b1/s1 [ Skip ]', ['Mac'])

  def testParseExpectationLineBadResultBracketSpacing(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    with self.assertRaises(expectations_parser.ParseError):
      parser._ParseExpectationLine(
          0, 'crbug.com/2345 [ Mac ] b1/s1 [Skip]', ['Mac'])

  def testParseExpectationLineNoClosingConditionBracket(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    with self.assertRaises(expectations_parser.ParseError):
      parser._ParseExpectationLine(
          0, 'crbug.com/2345 [ Mac b1/s1 [ Skip ]', ['Mac'])

  def testParseExpectationLineNoClosingResultBracket(self):
    parser = expectations_parser.TestExpectationParser(raw='#Empty')
    with self.assertRaises(expectations_parser.ParseError):
      parser._ParseExpectationLine(
          0, 'crbug.com/2345 [ Mac ] b1/s1 [ Skip', ['Mac'])
