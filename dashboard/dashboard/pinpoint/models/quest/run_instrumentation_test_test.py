# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from dashboard.pinpoint.models.quest import run_instrumentation_test

_BASE_ARGUMENTS = {
    'swarming_server': 'server',
    'dimensions': {'key': 'value'},
}


_BASE_EXTRA_ARGS = run_instrumentation_test._DEFAULT_EXTRA_ARGS


class FromDictTest(unittest.TestCase):

  def testMinimumArguments(self):
    quest = run_instrumentation_test.RunInstrumentationTest.FromDict(
        _BASE_ARGUMENTS)
    expected = run_instrumentation_test.RunInstrumentationTest(
        'server', {'key': 'value'}, _BASE_EXTRA_ARGS)
    self.assertEqual(quest, expected)

  def testAllArguments(self):
    arguments = dict(_BASE_ARGUMENTS)
    filter_string = 'InstrumentationClass#SomeTestCase'
    arguments['test-filter'] = filter_string
    arguments['num-retries'] = '0'
    arguments['num-repeats'] = '1'
    quest = run_instrumentation_test.RunInstrumentationTest.FromDict(arguments)

    extra_args = [
        '--test-filter', filter_string,
        '--num-retries', '0',
        '--repeat', '1'] + _BASE_EXTRA_ARGS
    expected = run_instrumentation_test.RunInstrumentationTest(
        'server', {'key': 'value'}, extra_args)
    self.assertEqual(quest, expected)

  def testNegativeRetries(self):
    arguments = dict(_BASE_ARGUMENTS)
    arguments['num-retries'] = '-1'
    with self.assertRaises(TypeError):
      run_instrumentation_test.RunInstrumentationTest.FromDict(arguments)

  def testNegativeRepeats(self):
    arguments = dict(_BASE_ARGUMENTS)
    arguments['num-repeats'] = '-1'
    with self.assertRaises(TypeError):
      run_instrumentation_test.RunInstrumentationTest.FromDict(arguments)
