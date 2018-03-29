# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import mock

from dashboard.pinpoint.models.quest import run_telemetry_test



_MIN_ARGUMENTS = [
    'speedometer', '--pageset-repeat', '1', '--browser', 'release',
    '-v', '--upload-results', '--output-format', 'histograms',
    '--isolated-script-test-output', '${ISOLATED_OUTDIR}/output.json',
    '--isolated-script-test-chartjson-output',
    '${ISOLATED_OUTDIR}/chartjson-output.json',
]


_ALL_ARGUMENTS = [
    'speedometer', '--story-filter', 'http://www.fifa.com/',
    '--pageset-repeat', '1', '--browser', 'release',
    '--custom-arg', 'custom value',
    '-v', '--upload-results', '--output-format', 'histograms',
    '--isolated-script-test-output', '${ISOLATED_OUTDIR}/output.json',
    '--isolated-script-test-chartjson-output',
    '${ISOLATED_OUTDIR}/chartjson-output.json',
]


_STARTUP_BENCHMARK_ARGUMENTS = [
    'start_with_url.warm.startup_pages',
    '--pageset-repeat', '2', '--browser', 'release',
    '-v', '--upload-results', '--output-format', 'histograms',
    '--isolated-script-test-output', '${ISOLATED_OUTDIR}/output.json',
    '--isolated-script-test-chartjson-output',
    '${ISOLATED_OUTDIR}/chartjson-output.json',
]


_WEBVIEW_ARGUMENTS = [
    'speedometer', '--pageset-repeat', '1', '--browser', 'android-webview',
    '-v', '--upload-results', '--output-format', 'histograms',
    '--isolated-script-test-output', '${ISOLATED_OUTDIR}/output.json',
    '--isolated-script-test-chartjson-output',
    '${ISOLATED_OUTDIR}/chartjson-output.json',
    '--webview-embedder-apk', '../../out/Release/apks/SystemWebViewShell.apk',
]


class StartTest(unittest.TestCase):

  @mock.patch.object(run_telemetry_test.run_test.RunTest, 'Start')
  def testStart(self, start):
    quest = run_telemetry_test.RunTelemetryTest({'key': 'value'}, [])
    quest.Start('change', 'isolate hash')
    start.assert_called_once_with('change', 'isolate hash',
                                  ['--results-label', 'change'])


class FromDictTest(unittest.TestCase):

  def testMissingDimensions(self):
    arguments = {
        'target': 'telemetry_perf_tests',
        'benchmark': 'speedometer',
        'browser': 'release',
    }
    with self.assertRaises(TypeError):
      run_telemetry_test.RunTelemetryTest.FromDict(arguments)

  def testMissingBenchmark(self):
    arguments = {
        'target': 'telemetry_perf_tests',
        'dimensions': '{"key": "value"}',
        'browser': 'release',
    }
    with self.assertRaises(TypeError):
      run_telemetry_test.RunTelemetryTest.FromDict(arguments)

  def testMissingBrowser(self):
    arguments = {
        'target': 'telemetry_perf_tests',
        'dimensions': '{"key": "value"}',
        'benchmark': 'speedometer',
    }
    with self.assertRaises(TypeError):
      run_telemetry_test.RunTelemetryTest.FromDict(arguments)

  def testMinimumArguments(self):
    arguments = {
        'target': 'telemetry_perf_tests',
        'dimensions': '{"key": "value"}',
        'benchmark': 'speedometer',
        'browser': 'release',
    }

    expected = run_telemetry_test.RunTelemetryTest(
        {'key': 'value'}, _MIN_ARGUMENTS)
    self.assertEqual(run_telemetry_test.RunTelemetryTest.FromDict(arguments),
                     expected)

  def testAllArguments(self):
    arguments = {
        'target': 'telemetry_perf_tests',
        'dimensions': '{"key": "value"}',
        'benchmark': 'speedometer',
        'browser': 'release',
        'story': 'http://www.fifa.com/',
        'extra_test_args': '["--custom-arg", "custom value"]',
    }

    expected = run_telemetry_test.RunTelemetryTest(
        {'key': 'value'}, _ALL_ARGUMENTS)
    self.assertEqual(run_telemetry_test.RunTelemetryTest.FromDict(arguments),
                     expected)

  def testDictDimensions(self):
    arguments = {
        'target': 'telemetry_perf_tests',
        'dimensions': {'key': 'value'},
        'benchmark': 'speedometer',
        'browser': 'release',
    }

    expected = run_telemetry_test.RunTelemetryTest(
        {'key': 'value'}, _MIN_ARGUMENTS)
    self.assertEqual(run_telemetry_test.RunTelemetryTest.FromDict(arguments),
                     expected)

  def testStringExtraTestArgs(self):
    arguments = {
        'target': 'telemetry_perf_tests',
        'dimensions': '{"key": "value"}',
        'benchmark': 'speedometer',
        'browser': 'release',
        'story': 'http://www.fifa.com/',
        'extra_test_args': '--custom-arg "custom value"',
    }

    expected = run_telemetry_test.RunTelemetryTest(
        {'key': 'value'}, _ALL_ARGUMENTS)
    self.assertEqual(run_telemetry_test.RunTelemetryTest.FromDict(arguments),
                     expected)

  def testInvalidExtraTestArgs(self):
    arguments = {
        'target': 'telemetry_perf_tests',
        'dimensions': '{"key": "value"}',
        'benchmark': 'speedometer',
        'browser': 'release',
        'extra_test_args': '"this is a string"',
    }

    with self.assertRaises(TypeError):
      run_telemetry_test.RunTelemetryTest.FromDict(arguments)

  def testStartupBenchmarkRepeatCount(self):
    arguments = {
        'target': 'telemetry_perf_tests',
        'dimensions': '{"key": "value"}',
        'benchmark': 'start_with_url.warm.startup_pages',
        'browser': 'release',
    }

    expected = run_telemetry_test.RunTelemetryTest(
        {'key': 'value'}, _STARTUP_BENCHMARK_ARGUMENTS)
    self.assertEqual(run_telemetry_test.RunTelemetryTest.FromDict(arguments),
                     expected)

  def testWebviewFlag(self):
    arguments = {
        'target': 'telemetry_perf_webview_tests',
        'dimensions': '{"key": "value"}',
        'benchmark': 'speedometer',
        'browser': 'android-webview',
    }

    expected = run_telemetry_test.RunTelemetryTest(
        {'key': 'value'}, _WEBVIEW_ARGUMENTS)
    self.assertEqual(run_telemetry_test.RunTelemetryTest.FromDict(arguments),
                     expected)
