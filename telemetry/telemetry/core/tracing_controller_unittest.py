# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import time
import unittest

from battor import battor_wrapper
from telemetry import decorators
from telemetry.util import trace_runner
from telemetry.internal.browser import browser_finder
from telemetry.testing import options_for_unittests
from telemetry.testing import tab_test_case
from telemetry.timeline import model as model_module
from telemetry.timeline import tracing_config

from tracing.trace_data import trace_data as trace_data_module


TEST_MARKER_PREFIX = 'test-marker-'


def InjectMarker(tab, label):
  marker = TEST_MARKER_PREFIX + str(label)
  tab.EvaluateJavaScript('console.time({{ marker }});', marker=marker)
  tab.EvaluateJavaScript('console.timeEnd({{ marker }});', marker=marker)


def ReadMarkerEvents(trace_data):
  # Parse the trace and extract all test markers & trace-flushing markers
  return trace_runner.ExecuteMappingCodeOnTraceData(
      trace_data, """
function processTrace(results, model) {
    var markers = [];
    for (const thread of model.getAllThreads()) {
        for (const event of thread.asyncSliceGroup.slices) {
            if (event.title.startsWith('test-marker-') ||
                event.title === 'flush-tracing') {
                markers.push({'title': event.title, 'start': event.start});
           }
       }
   }
   results.addPair('markers', markers);
};
       """)['markers']


class TracingControllerTest(tab_test_case.TabTestCase):
  """Tests that start tracing when a browser tab is already active."""

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
    InjectMarker(tab, 0)

    # Flush tracing |subtrace_count - 1| times and inject a unique marker into
    # the sub-trace each time.
    for i in xrange(1, subtrace_count):
      tracing_controller.FlushTracing()
      self.assertTrue(tracing_controller.is_tracing_running)
      InjectMarker(tab, i)

    # Stop tracing.
    trace_data, errors = tracing_controller.StopTracing()
    self.assertEqual(errors, [])
    self.assertFalse(tracing_controller.is_tracing_running)

    # Check that the markers 'test-marker-0', 'flush-tracing',
    # 'test-marker-1', ..., 'flush-tracing',
    # 'test-marker-|subtrace_count - 1|' are monotonic.
    markers = ReadMarkerEvents(trace_data)
    self.assertEquals(2 * subtrace_count - 1, len(markers))
    for i in xrange(0, len(markers) - 2):
      if i % 2 == 0:
        expected_title = 'test-marker-%d' % (i/2)
      else:
        expected_title = 'flush-tracing'
      self.assertEquals(expected_title, markers[i]['title'])
      self.assertLess(markers[i]['start'], markers[i + 1]['start'])

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


class StartupTracingTest(unittest.TestCase):
  """Tests that start tracing before the browser is created."""

  def setUp(self):
    finder_options = options_for_unittests.GetCopy()
    self.possible_browser = browser_finder.FindBrowser(finder_options)
    if not self.possible_browser:
      raise Exception('No browser found, cannot continue test.')
    self.browser_options = finder_options.browser_options
    self.config = tracing_config.TracingConfig()
    self.config.enable_chrome_trace = True

  def tearDown(self):
    if self.possible_browser and self.tracing_controller.is_tracing_running:
      self.tracing_controller.StopTracing()

  @property
  def tracing_controller(self):
    return self.possible_browser.platform.tracing_controller

  def StopTracingAndGetTestMarkers(self):
    self.assertTrue(self.tracing_controller.is_tracing_running)
    trace_data, errors = self.tracing_controller.StopTracing()
    self.assertFalse(self.tracing_controller.is_tracing_running)
    self.assertEqual(errors, [])
    return [
        e['title'][len(TEST_MARKER_PREFIX):]
        for e in ReadMarkerEvents(trace_data)
        if e['title'].startswith(TEST_MARKER_PREFIX)]

  @decorators.Isolated
  def testStopTracingWhileBrowserIsRunning(self):
    self.tracing_controller.StartTracing(self.config)
    with self.possible_browser.BrowserSession(self.browser_options) as browser:
      browser.tabs[0].Navigate('about:blank')
      browser.tabs[0].WaitForDocumentReadyStateToBeInteractiveOrBetter()
      InjectMarker(browser.tabs[0], 'foo')
      markers = self.StopTracingAndGetTestMarkers()
    self.assertEquals(markers, ['foo'])

  @decorators.Isolated
  def testCloseBrowserBeforeTracingIsStopped(self):
    self.tracing_controller.StartTracing(self.config)
    with self.possible_browser.BrowserSession(self.browser_options) as browser:
      browser.tabs[0].Navigate('about:blank')
      browser.tabs[0].WaitForDocumentReadyStateToBeInteractiveOrBetter()
      InjectMarker(browser.tabs[0], 'bar')
      # TODO(crbug.com/854212): This should happen implicitly on browser.Close()
      self.tracing_controller.FlushTracing()
    markers = self.StopTracingAndGetTestMarkers()
    self.assertEquals(markers, ['bar'])

  @decorators.Isolated
  def testRestartBrowserWhileTracing(self):
    expected_markers = ['browser-%i' % i for i in xrange(1, 4)]
    self.tracing_controller.StartTracing(self.config)
    try:
      self.possible_browser.SetUpEnvironment(self.browser_options)
      for marker in expected_markers:
        with self.possible_browser.Create() as browser:
          browser.tabs[0].Navigate('about:blank')
          browser.tabs[0].WaitForDocumentReadyStateToBeInteractiveOrBetter()
          InjectMarker(browser.tabs[0], marker)
          # TODO(crbug.com/854212): This should happen implicitly.
          self.tracing_controller.FlushTracing()
    finally:
      self.possible_browser.CleanUpEnvironment()
    markers = self.StopTracingAndGetTestMarkers()
    # Markers may be out of order.
    self.assertItemsEqual(markers, expected_markers)
