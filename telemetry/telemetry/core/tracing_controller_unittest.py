# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import time
import unittest

from battor import battor_wrapper
from telemetry import decorators
from telemetry.internal.browser import browser_finder
from telemetry.testing import options_for_unittests
from telemetry.testing import tab_test_case
from telemetry.timeline import model as model_module
from telemetry.timeline import tracing_config
from tracing.trace_data import trace_data as trace_data_module


def InjectMarker(tab, marker):
  tab.EvaluateJavaScript('console.time({{ marker }});', marker=marker)
  tab.EvaluateJavaScript('console.timeEnd({{ marker }});', marker=marker)


class TracingControllerTest(tab_test_case.TabTestCase):

  @decorators.Isolated
  def testExceptionRaisedInStopTracing(self):
    tracing_controller = self._tab.browser.platform.tracing_controller
    config = tracing_config.TracingConfig()
    config.enable_chrome_trace = True
    tracing_controller.StartTracing(config)

    self.Navigate('blank.html')

    def _FakeStopChromeTracing(*args):
      del args  # Unused
      raise Exception('Intentional Tracing Exception')

    self._tab._inspector_backend._devtools_client.StopChromeTracing = (
        _FakeStopChromeTracing)
    with self.assertRaisesRegexp(Exception, 'Intentional Tracing Exception'):
      tracing_controller.StopTracing()

    # Tracing is stopped even if there is exception.
    self.assertFalse(tracing_controller.is_tracing_running)

  @decorators.Isolated
  def testGotTrace(self):
    tracing_controller = self._browser.platform.tracing_controller
    config = tracing_config.TracingConfig()
    config.enable_chrome_trace = True
    tracing_controller.StartTracing(config)

    trace_data, errors = tracing_controller.StopTracing()
    self.assertEqual(errors, [])
    # Test that trace data is parsable
    model = model_module.TimelineModel(trace_data)
    assert len(model.processes) > 0

  @decorators.Isolated
  def testStartAndStopTraceMultipleTimes(self):
    tracing_controller = self._browser.platform.tracing_controller
    config = tracing_config.TracingConfig()
    config.enable_chrome_trace = True
    tracing_controller.StartTracing(config)
    self.assertFalse(tracing_controller.StartTracing(config))

    trace_data, errors = tracing_controller.StopTracing()
    self.assertEqual(errors, [])
    # Test that trace data is parsable
    model_module.TimelineModel(trace_data)
    self.assertFalse(tracing_controller.is_tracing_running)
    # Calling stop again will raise exception
    self.assertRaises(Exception, tracing_controller.StopTracing)

  @decorators.Isolated
  @decorators.Disabled('win')  # crbug.com/829976
  def testFlushTracing(self):
    subtrace_count = 5

    tab = self._browser.tabs[0]

    # Set up the tracing config.
    tracing_controller = self._browser.platform.tracing_controller
    config = tracing_config.TracingConfig()
    config.enable_chrome_trace = True

    # Start tracing and inject a unique marker into the sub-trace.
    tracing_controller.StartTracing(config)
    self.assertTrue(tracing_controller.is_tracing_running)
    InjectMarker(tab, 'test-marker-0')

    # Flush tracing |subtrace_count - 1| times and inject a unique marker into
    # the sub-trace each time.
    for i in xrange(1, subtrace_count):
      tracing_controller.FlushTracing()
      self.assertTrue(tracing_controller.is_tracing_running)
      InjectMarker(tab, 'test-marker-%d' % i)

    # Stop tracing.
    trace_data, errors = tracing_controller.StopTracing()
    self.assertEqual(errors, [])
    self.assertFalse(tracing_controller.is_tracing_running)

    # Test that trace data is parsable
    model = model_module.TimelineModel(trace_data)

    # Check that the markers 'test-marker-0', 'flush-tracing', 'test-marker-1',
    # ..., 'flush-tracing', 'test-marker-|subtrace_count - 1|' are monotonic.
    custom_markers = [
        marker
        for i in xrange(subtrace_count)
        for marker in model.FindTimelineMarkers('test-marker-%d' % i)
    ]
    flush_markers = model.FindTimelineMarkers(['flush-tracing'] *
                                              (subtrace_count - 1))
    markers = [
        marker for group in zip(custom_markers, flush_markers)
        for marker in group
    ] + custom_markers[-1:]

    self.assertEquals(len(custom_markers), subtrace_count)
    self.assertEquals(len(flush_markers), subtrace_count - 1)
    self.assertEquals(len(markers), 2 * subtrace_count - 1)

    for i in xrange(1, len(markers)):
      self.assertLess(markers[i - 1].end, markers[i].start)

  @decorators.Disabled('linux')  # crbug.com/673761
  def testBattOrTracing(self):
    test_platform = self._browser.platform.GetOSName()
    device = (self._browser.platform._platform_backend.device
              if test_platform == 'android' else None)
    if (not battor_wrapper.IsBattOrConnected(
        test_platform, android_device=device)):
      return  # Do not run the test if no BattOr is connected.

    tracing_controller = self._browser.platform.tracing_controller
    config = tracing_config.TracingConfig()
    config.enable_battor_trace = True
    tracing_controller.StartTracing(config)
    # We wait 1s before starting and stopping tracing to avoid crbug.com/602266,
    # which would cause a crash otherwise.
    time.sleep(1)
    trace_data, errors = tracing_controller.StopTracing()
    self.assertEqual(errors, [])
    self.assertTrue(
        trace_data.HasTracesFor(trace_data_module.BATTOR_TRACE_PART))


class BrowserStartupTracingTest(unittest.TestCase):
  # https://github.com/catapult-project/catapult/issues/3099 (Android)
  @decorators.Disabled('android')
  @decorators.Isolated
  def testStartupTracing(self):
    finder_options = options_for_unittests.GetCopy()
    possible_browser = browser_finder.FindBrowser(finder_options)
    if not possible_browser:
      raise Exception('No browser found, cannot continue test.')
    platform = possible_browser.platform

    # Start tracing
    self.assertFalse(platform.tracing_controller.is_tracing_running)
    config = tracing_config.TracingConfig()
    config.enable_chrome_trace = True
    platform.tracing_controller.StartTracing(config)
    self.assertTrue(platform.tracing_controller.is_tracing_running)

    try:
      # Start browser
      with possible_browser.BrowserSession(
          finder_options.browser_options) as browser:
        browser.tabs[0].Navigate('about:blank')
        browser.tabs[0].WaitForDocumentReadyStateToBeInteractiveOrBetter()

        # Calling start tracing again will return False
        self.assertFalse(platform.tracing_controller.StartTracing(config))

        trace_data, errors = platform.tracing_controller.StopTracing()
        self.assertEqual(errors, [])
        # Test that trace data is parseable
        model_module.TimelineModel(trace_data)
        self.assertFalse(platform.tracing_controller.is_tracing_running)
        # Calling stop tracing again will raise exception
        with self.assertRaises(Exception):
          platform.tracing_controller.StopTracing()
    finally:
      if platform.tracing_controller.is_tracing_running:
        platform.tracing_controller.StopTracing()


class BrowserShutdownTracingTest(unittest.TestCase):
  """ Test ensuring the tracing are still collected from browsers that closed
  before tracing_controller.StopTracing() is called.

  """
  @decorators.Isolated
  def testBrowserShutdownTracing(self):
    finder_options = options_for_unittests.GetCopy()
    possible_browser = browser_finder.FindBrowser(finder_options)
    if not possible_browser:
      raise Exception('No browser found, cannot continue test.')
    platform = possible_browser.platform

    # Start tracing
    self.assertFalse(platform.tracing_controller.is_tracing_running)
    config = tracing_config.TracingConfig()
    config.enable_chrome_trace = True
    platform.tracing_controller.StartTracing(config)
    self.assertTrue(platform.tracing_controller.is_tracing_running)

    try:
      possible_browser.SetUpEnvironment(finder_options.browser_options)

      # Start two browsers
      browser_1 = possible_browser.Create()
      browser_2 = possible_browser.Create()

      browser_1.tabs[0].Navigate('about:blank')
      browser_1.tabs[0].WaitForDocumentReadyStateToBeInteractiveOrBetter()
      InjectMarker(browser_1.tabs[0], 'Browser-1')

      browser_2.tabs[0].Navigate('about:blank')
      browser_2.tabs[0].WaitForDocumentReadyStateToBeInteractiveOrBetter()
      InjectMarker(browser_2.tabs[0], 'Browser-2')

      # Close browser 1, then stop tracing, then close browser 2
      browser_1.Close()
      trace_data, errors = platform.tracing_controller.StopTracing()
      browser_2.Close()

      self.assertEqual(errors, [])

      # Test that trace data is parseable
      model = model_module.TimelineModel(trace_data)

      # Check that the markers 'Browser-1' and 'Browser-2' can be found in the
      # trace.
      self.assertTrue(model.FindTimelineMarkers('Browser-1'))
      self.assertTrue(model.FindTimelineMarkers('Browser-2'))

      self.assertFalse(platform.tracing_controller.is_tracing_running)
    finally:
      possible_browser.CleanUpEnvironment()
      #if platform.tracing_controller.is_tracing_running:
      #  platform.tracing_controller.StopTracing()
