# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from dashboard.pinpoint.models.quest import run_gtest


_MIN_ARGUMENTS = [
    '--gtest_repeat=1',
    '--isolated-script-test-output', '${ISOLATED_OUTDIR}/output.json',
    '--isolated-script-test-chartjson-output',
    '${ISOLATED_OUTDIR}/chartjson-output.json',
]


_ALL_ARGUMENTS = [
    '--gtest_filter=test_name', '--gtest_repeat=1',
    '--custom-arg', 'custom value',
    '--isolated-script-test-output', '${ISOLATED_OUTDIR}/output.json',
    '--isolated-script-test-chartjson-output',
    '${ISOLATED_OUTDIR}/chartjson-output.json',
]


class FromDictTest(unittest.TestCase):

  def testMinimumArguments(self):
    arguments = {
        'target': 'net_perftests',
        'dimensions': '{"key": "value"}',
    }

    expected = run_gtest.RunGTest({'key': 'value'}, _MIN_ARGUMENTS)
    self.assertEqual(run_gtest.RunGTest.FromDict(arguments), expected)

  def testAllArguments(self):
    arguments = {
        'target': 'net_perftests',
        'dimensions': '{"key": "value"}',
        'test': 'test_name',
        'extra_test_args': '["--custom-arg", "custom value"]',
    }

    expected = run_gtest.RunGTest(
        {'key': 'value'}, _ALL_ARGUMENTS)
    self.assertEqual(run_gtest.RunGTest.FromDict(arguments), expected)

  def testDictDimensions(self):
    arguments = {
        'target': 'net_perftests',
        'dimensions': {'key': 'value'},
    }

    expected = run_gtest.RunGTest({'key': 'value'}, _MIN_ARGUMENTS)
    self.assertEqual(run_gtest.RunGTest.FromDict(arguments), expected)
