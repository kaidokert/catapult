# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import optparse
import os
import unittest

from telemetry import benchmark
from telemetry.internal.backends.chrome import android_browser_finder
from telemetry.internal.backends.chrome import cros_browser_finder
from telemetry.internal.backends.chrome import desktop_browser_finder
from telemetry.internal.browser import browser_finder
from telemetry.internal.browser import browser_options
from telemetry.internal.platform import android_device
from telemetry.internal.platform import cros_device
from telemetry.internal.platform import desktop_device
from telemetry.internal.platform import device_finder
from telemetry.story import expectations


class BrowserOptionsTest(unittest.TestCase):
  def testBrowserMultipleValues_UseLast(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()
    parser.parse_args(['--browser=stable', '--browser=reference'])
    self.assertEqual(
        options.browser_type, 'reference',
        'Note that this test is needed for run_performance_tests.py.'
        'See crbug.com/928928.')

  def testDefaults(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()
    parser.add_option('-x', action='store', default=3)
    parser.parse_args(['--browser', 'any'])
    self.assertEquals(options.x, 3) # pylint: disable=no-member

  def testDefaultsPlusOverride(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()
    parser.add_option('-x', action='store', default=3)
    parser.parse_args(['--browser', 'any', '-x', 10])
    self.assertEquals(options.x, 10) # pylint: disable=no-member

  def testDefaultsDontClobberPresetValue(self):
    options = browser_options.BrowserFinderOptions()
    setattr(options, 'x', 7)
    parser = options.CreateParser()
    parser.add_option('-x', action='store', default=3)
    parser.parse_args(['--browser', 'any'])
    self.assertEquals(options.x, 7) # pylint: disable=no-member

  def testCount0(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()
    parser.add_option('-x', action='count', dest='v')
    parser.parse_args(['--browser', 'any'])
    self.assertEquals(options.v, None) # pylint: disable=no-member

  def testCount2(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()
    parser.add_option('-x', action='count', dest='v')
    parser.parse_args(['--browser', 'any', '-xx'])
    self.assertEquals(options.v, 2) # pylint: disable=no-member

  def testOptparseMutabilityWhenSpecified(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()
    parser.add_option('-x', dest='verbosity', action='store_true')
    options_ret, _ = parser.parse_args(['--browser', 'any', '-x'])
    self.assertEquals(options_ret, options)
    self.assertTrue(options.verbosity)

  def testOptparseMutabilityWhenNotSpecified(self):
    options = browser_options.BrowserFinderOptions()

    parser = options.CreateParser()
    parser.add_option('-x', dest='verbosity', action='store_true')
    options_ret, _ = parser.parse_args(['--browser', 'any'])
    self.assertEquals(options_ret, options)
    self.assertFalse(options.verbosity)

  def testProfileDirDefault(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()
    parser.parse_args(['--browser', 'any'])
    self.assertEquals(options.browser_options.profile_dir, None)

  def testProfileDir(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()
    # Need to use a directory that exists.
    current_dir = os.path.dirname(__file__)
    parser.parse_args(['--browser', 'any', '--profile-dir', current_dir])
    self.assertEquals(options.browser_options.profile_dir, current_dir)

  def testExtraBrowserArgs(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()
    parser.parse_args(['--extra-browser-args=--foo --bar'])

    self.assertEquals(options.browser_options.extra_browser_args,
                      set(['--foo', '--bar']))

  def testEnableSystrace(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()
    parser.parse_args(['--enable-systrace'])

    self.assertTrue(options.enable_systrace)

  def testIncompatibleIntervalProfilingPeriods(self):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser()

    with self.assertRaises(SystemExit) as context:
      parser.parse_args(['--interval-profiling-period=story_run',
                         '--interval-profiling-period=navigation'])
    self.assertEqual(context.exception.code, 1)

  def testMergeDefaultValues(self):
    options = browser_options.BrowserFinderOptions()
    options.already_true = True
    options.already_false = False
    options.override_to_true = False
    options.override_to_false = True

    parser = optparse.OptionParser()
    parser.add_option('--already_true', action='store_true')
    parser.add_option('--already_false', action='store_true')
    parser.add_option('--unset', action='store_true')
    parser.add_option('--default_true', action='store_true', default=True)
    parser.add_option('--default_false', action='store_true', default=False)
    parser.add_option('--override_to_true', action='store_true', default=False)
    parser.add_option('--override_to_false', action='store_true', default=True)

    options.MergeDefaultValues(parser.get_default_values())

    self.assertTrue(options.already_true)
    self.assertFalse(options.already_false)
    self.assertTrue(options.unset is None)
    self.assertTrue(options.default_true)
    self.assertFalse(options.default_false)
    self.assertFalse(options.override_to_true)
    self.assertTrue(options.override_to_false)

  def testBrowserAndDeviceFinders(self):
    options = browser_options.BrowserFinderOptions()
    browser_finders = browser_finder.GetBrowserFinders(options.target_platforms)
    self.assertTrue(android_browser_finder in browser_finders)
    self.assertTrue(cros_browser_finder in browser_finders)
    self.assertTrue(desktop_browser_finder in browser_finders)
    device_finders = device_finder.GetDeviceFinders(options.target_platforms)
    self.assertTrue(android_device in device_finders)
    self.assertTrue(cros_device in device_finders)
    self.assertTrue(desktop_device in device_finders)

    @benchmark.Owner(emails=['bob@chromium.org'], component='xyzzyx')
    class DesktopBenchmark(benchmark.Benchmark):
      SUPPORTED_PLATFORMS = [expectations.ALL_DESKTOP]
      @classmethod
      def Name(cls):
        return "desktop"

    options.target_platforms = DesktopBenchmark().GetSupportedPlatforms()
    browser_finders = browser_finder.GetBrowserFinders(options.target_platforms)
    self.assertFalse(android_browser_finder in browser_finders)
    self.assertTrue(cros_browser_finder in browser_finders)
    self.assertTrue(desktop_browser_finder in browser_finders)
    device_finders = device_finder.GetDeviceFinders(options.target_platforms)
    self.assertFalse(android_device in device_finders)
    self.assertTrue(cros_device in device_finders)
    self.assertTrue(desktop_device in device_finders)

    @benchmark.Owner(emails=['bob@chromium.org'], component='xyzzyx')
    class AndroidBenchmark(benchmark.Benchmark):
      SUPPORTED_PLATFORMS = [expectations.ALL_ANDROID]
      @classmethod
      def Name(cls):
        return "android"

    options.target_platforms = AndroidBenchmark().GetSupportedPlatforms()
    browser_finders = browser_finder.GetBrowserFinders(options.target_platforms)
    self.assertTrue(android_browser_finder in browser_finders)
    self.assertFalse(cros_browser_finder in browser_finders)
    self.assertFalse(desktop_browser_finder in browser_finders)
    device_finders = device_finder.GetDeviceFinders(options.target_platforms)
    self.assertTrue(android_device in device_finders)
    self.assertFalse(cros_device in device_finders)
    self.assertFalse(desktop_device in device_finders)

    @benchmark.Owner(emails=['bob@chromium.org'], component='xyzzyx')
    class MacBenchmark(benchmark.Benchmark):
      SUPPORTED_PLATFORMS = [expectations.MAC_10_11]
      @classmethod
      def Name(cls):
        return "Mac 10.11"

    options.target_platforms = MacBenchmark().GetSupportedPlatforms()
    browser_finders = browser_finder.GetBrowserFinders(options.target_platforms)
    self.assertFalse(android_browser_finder in browser_finders)
    self.assertFalse(cros_browser_finder in browser_finders)
    self.assertTrue(desktop_browser_finder in browser_finders)
    device_finders = device_finder.GetDeviceFinders(options.target_platforms)
    self.assertFalse(android_device in device_finders)
    self.assertFalse(cros_device in device_finders)
    self.assertTrue(desktop_device in device_finders)

    @benchmark.Owner(emails=['bob@chromium.org'], component='xyzzyx')
    class WebViewBenchmark(benchmark.Benchmark):
      SUPPORTED_PLATFORMS = [expectations.ANDROID_NEXUS6_WEBVIEW]
      @classmethod
      def Name(cls):
        return "Android WebView"

    options.target_platforms = WebViewBenchmark().GetSupportedPlatforms()
    browser_finders = browser_finder.GetBrowserFinders(options.target_platforms)
    self.assertTrue(android_browser_finder in browser_finders)
    self.assertFalse(cros_browser_finder in browser_finders)
    self.assertFalse(desktop_browser_finder in browser_finders)
    device_finders = device_finder.GetDeviceFinders(options.target_platforms)
    self.assertTrue(android_device in device_finders)
    self.assertFalse(cros_device in device_finders)
    self.assertFalse(desktop_device in device_finders)
