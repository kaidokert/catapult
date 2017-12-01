# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


import unittest

from py_utils import expectations_parser


class TestExpectationParserTest(unittest.TestCase):

  def AssertExpectationsEqual(self, actual, expected):
    for i in range(len(actual)):
      self.assertEqual(actual[i].reason, expected[i].reason)
      self.assertEqual(actual[i].test, expected[i].test)
      self.assertEqual(actual[i].conditions, expected[i].conditions)
      self.assertEqual(actual[i].results, expected[i].results)

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
        expectations_parser.Expectation(
            'crbug.com/12345', 'b1/s1', ['Mac'], ['Skip']),
        expectations_parser.Expectation(
            'crbug.com/23456', 'b1/s2', ['Mac', 'Debug'], ['Skip'])
    ]
    self.AssertExpectationsEqual(parser.expectations, expected_outcome)

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
    raw_data = '# tags: Mac\ncrbug.com/23456 [ Mac ] b1/s2 [ Skip ]'
    parser = expectations_parser.TestExpectationParser(raw=raw_data)
    expected_outcome = [
        expectations_parser.Expectation(
            'crbug.com/23456', 'b1/s2', ['Mac'], ['Skip'])
    ]
    self.AssertExpectationsEqual(parser.expectations, expected_outcome)

  def testParseExpectationLineBadTag(self):
    raw_data = '# tags: None\ncrbug.com/23456 [ Mac ] b1/s2 [ Skip ]'
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(raw=raw_data)

  def testParseExpectationLineNoConditions(self):
    raw_data = '# tags: All\ncrbug.com/12345 b1/s1 [ Skip ]'
    parser = expectations_parser.TestExpectationParser(raw=raw_data)
    expected_outcome = [
        expectations_parser.Expectation(
            'crbug.com/12345', 'b1/s1', [], ['Skip']),
    ]
    self.AssertExpectationsEqual(parser.expectations, expected_outcome)

  def testParseExpectationLineNoBug(self):
    raw_data = '# tags: All\n[ All ] b1/s1 [ Skip ]'
    parser = expectations_parser.TestExpectationParser(raw=raw_data)
    expected_outcome = [
        expectations_parser.Expectation(
            None, 'b1/s1', ['All'], ['Skip']),
    ]
    self.AssertExpectationsEqual(parser.expectations, expected_outcome)

  def testParseExpectationLineNoBugNoConditions(self):
    raw_data = '# tags: All\nb1/s1 [ Skip ]'
    parser = expectations_parser.TestExpectationParser(raw=raw_data)
    expected_outcome = [
        expectations_parser.Expectation(
            None, 'b1/s1', [], ['Skip']),
    ]
    self.AssertExpectationsEqual(parser.expectations, expected_outcome)

  def testParseExpectationLineMultipleConditions(self):
    raw_data = ('# tags:All None Batman\n'
                'crbug.com/123 [ All None Batman ] b1/s1 [ Skip ]')
    parser = expectations_parser.TestExpectationParser(raw=raw_data)
    expected_outcome = [
        expectations_parser.Expectation(
            'crbug.com/123', 'b1/s1', ['All', 'None', 'Batman'], ['Skip']),
    ]
    self.AssertExpectationsEqual(parser.expectations, expected_outcome)

  def testParseExpectationLineBadConditionBracket(self):
    raw_data = '# tags: Mac\ncrbug.com/23456 ] Mac ] b1/s2 [ Skip ]'
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(raw=raw_data)

  def testParseExpectationLineBadResultBracket(self):
    raw_data = '# tags: Mac\ncrbug.com/23456 ] Mac ] b1/s2 ] Skip ]'
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(raw=raw_data)

  def testParseExpectationLineBadConditionBracketSpacing(self):
    raw_data = '# tags: Mac\ncrbug.com/2345 [Mac] b1/s1 [ Skip ]'
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(raw=raw_data)

  def testParseExpectationLineBadResultBracketSpacing(self):
    raw_data = '# tags: Mac\ncrbug.com/2345 [ Mac ] b1/s1 [Skip]'
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(raw=raw_data)

  def testParseExpectationLineNoClosingConditionBracket(self):
    raw_data = '# tags: Mac\ncrbug.com/2345 [ Mac b1/s1 [ Skip ]'
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(raw=raw_data)

  def testParseExpectationLineNoClosingResultBracket(self):
    raw_data = '# tags: Mac\ncrbug.com/2345 [ Mac ] b1/s1 [ Skip'
    with self.assertRaises(expectations_parser.ParseError):
      expectations_parser.TestExpectationParser(raw=raw_data)
