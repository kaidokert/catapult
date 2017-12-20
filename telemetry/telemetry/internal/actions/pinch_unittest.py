# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import time

from telemetry import decorators
from telemetry.internal.actions import page_action
from telemetry.internal.actions import pinch
from telemetry.internal.actions import utils
from telemetry.testing import tab_test_case


class PinchActionTest(tab_test_case.TabTestCase):
  # TODO(bokan): Until recently, the coordinate system used by gpuBenchmarking
  # was broken when the page was zoomed in. This would cause "touches out of
  # screen bounds" crashes. This was fixed in a series of patches (see
  # https://crrev.com/c/668376) but requires a browser M63+. Until that rolls
  # into ref builds we can check this flag to only run tests on more recent
  # browsers.
  def _browserHasCorrectedZoomCoordinates(self):
    return self._tab.EvaluateJavaScript(
        '"gesturesExpectedInViewportCoordinates" in chrome.gpuBenchmarking')

  def setUp(self):
    super(PinchActionTest, self).setUp()
    self.Navigate('zoom.html')
    utils.InjectJavaScript(self._tab, 'gesture_common.js')

  def testPinchByApiCalledWithCorrectArguments(self):
    if not page_action.IsGestureSourceTypeSupported(self._tab, 'touch'):
      return

    action_runner = self._tab.action_runner
    action_runner.ExecuteJavaScript('''
        chrome.gpuBenchmarking.pinchBy = function(
            scaleFactor, anchorLeft, anchorTop, callback, speed) {
          window.__test_scaleFactor = scaleFactor;
          window.__test_anchorLeft = anchorLeft;
          window.__test_anchorTop = anchorTop;
          window.__test_callback = callback;
          window.__test_speed = speed;
          window.__pinchActionDone = true;
        };''')
    action_runner.PinchPage(scale_factor=2)
    self.assertEqual(
        2, action_runner.EvaluateJavaScript('window.__test_scaleFactor'))
    self.assertTrue(
        action_runner.EvaluateJavaScript('!isNaN(window.__test_anchorLeft)'))
    self.assertTrue(
        action_runner.EvaluateJavaScript('!isNaN(window.__test_anchorTop)'))
    self.assertTrue(
        action_runner.EvaluateJavaScript('!!window.__test_callback'))
    self.assertEqual(
        800, action_runner.EvaluateJavaScript('window.__test_speed'))

  def testPinchSpeed(self):
    # Testing actual speed is tricky since we need details about the device's
    # gesture recognizer. Instead, we'll just make sure that the speed is
    # invariant under zoom.

    if not self._browserHasCorrectedZoomCoordinates():
      return

    startTime = time.time()

    i = pinch.PinchAction(
        scale_factor=4,
        speed_in_pixels_per_second=500)
    i.WillRunAction(self._tab)
    i.RunAction(self._tab)

    deltaSeconds = time.time() - startTime

    startTime = time.time()

    i = pinch.PinchAction(
        scale_factor=0.25,
        speed_in_pixels_per_second=500)
    i.WillRunAction(self._tab)
    i.RunAction(self._tab)

    newDeltaSeconds = time.time() - startTime

    # Timing will always be a bit fuzzy. Additionally, slop affects the
    # distance differently when zooming in and out (the gesture scales faster
    # per pixel when close to the anchor) so we'll get some difference from
    # that too. So just make sure we're in the same ballpark.
    # TODO(bokan): I landed changes in M65 (https://crrev.com/c/784213) that
    # should make this significantly better. We can tighten up the bounds once
    # that's in ref builds.
    self.assertLess(abs(deltaSeconds - newDeltaSeconds) / deltaSeconds, 0.5)

  # TODO(bokan): It looks like pinch gestures don't quite work correctly on
  # desktop. Disable for now and investigate later. https://crbug.com/787615
  @decorators.Disabled('linux', 'mac', 'win')
  def testPinchScale(self):
    if not self._browserHasCorrectedZoomCoordinates():
      return

    # TODO(bokan): These can soon be converted to use window.visualViewport,
    # once the reference builds hit M61.

    starting_scale = self._tab.EvaluateJavaScript(
        'chrome.gpuBenchmarking.pageScaleFactor()')

    i = pinch.PinchAction(
        scale_factor=4,
        speed_in_pixels_per_second=500)
    i.WillRunAction(self._tab)
    i.RunAction(self._tab)

    scale = self._tab.EvaluateJavaScript(
        'chrome.gpuBenchmarking.pageScaleFactor()')

    self.assertLess(abs(starting_scale * 4 - scale), 0.2 * scale)

    starting_scale = scale

    i = pinch.PinchAction(
        scale_factor=0.5,
        speed_in_pixels_per_second=500)
    i.WillRunAction(self._tab)
    i.RunAction(self._tab)

    scale = self._tab.EvaluateJavaScript(
        'chrome.gpuBenchmarking.pageScaleFactor()')

    # Note: we have to use an approximate equality here. The pinch gestures
    # aren't exact. Some investigation long ago showed that the touch slop
    # distance in Android's gesture recognizer violated some assumptions made
    # by the synthetic gestures. There's (a bit of) context in
    # https://crbug.com/686390.
    # TODO(bokan): I landed changes in M65 (https://crrev.com/c/784213) that
    # should make this significantly better. We can tighten up the bounds once
    # that's in ref builds.
    self.assertLess(abs(starting_scale / 2 - scale), 0.2 * scale)

  # Test that the anchor ratio correctly centers the pinch gesture at the
  # requested part of the viewport.
  # TODO(bokan): It looks like pinch gestures don't quite work correctly on
  # desktop. Disable for now and investigate later. https://crbug.com/787615
  @decorators.Disabled('linux', 'mac', 'win')
  def testPinchAnchor(self):
    # TODO(bokan): These can soon be converted to use window.visualViewport,
    # once the reference builds hit M61.

    starting_scale = self._tab.EvaluateJavaScript(
        'chrome.gpuBenchmarking.pageScaleFactor()')
    self.assertEquals(1, starting_scale)

    width = self._tab.EvaluateJavaScript('__GestureCommon_GetWindowWidth();')
    height = self._tab.EvaluateJavaScript('__GestureCommon_GetWindowHeight();')

    # Pinch zoom into the bottom right corner. Note, we can't go exactly to the
    # corner since the starting touch point would be outside the screen.
    i = pinch.PinchAction(
        left_anchor_ratio=0.9,
        top_anchor_ratio=0.9,
        scale_factor=2.5,
        speed_in_pixels_per_second=500)
    i.WillRunAction(self._tab)
    i.RunAction(self._tab)

    offset_x = self._tab.EvaluateJavaScript(
        'chrome.gpuBenchmarking.visualViewportX()')
    offset_y = self._tab.EvaluateJavaScript(
        'chrome.gpuBenchmarking.visualViewportY()')

    self.assertGreater(offset_x, width / 2)
    self.assertGreater(offset_y, height / 2)

    # TODO(bokan): This early-out can be removed once setPageScaleFactor (M64)
    # rolls into the ref builds.
    if not self._tab.EvaluateJavaScript(
        "'setPageScaleFactor' in chrome.gpuBenchmarking"):
      return

    self._tab.EvaluateJavaScript(
        'chrome.gpuBenchmarking.setPageScaleFactor(1)')

    # Try again in the top left.
    i = pinch.PinchAction(
        left_anchor_ratio=0.1,
        top_anchor_ratio=0.1,
        scale_factor=2.5,
        speed_in_pixels_per_second=500)
    i.WillRunAction(self._tab)
    i.RunAction(self._tab)

    offset_x = self._tab.EvaluateJavaScript(
        'chrome.gpuBenchmarking.visualViewportX()')
    offset_y = self._tab.EvaluateJavaScript(
        'chrome.gpuBenchmarking.visualViewportY()')

    self.assertLess(offset_x + width / 2.5, width / 2)
    self.assertLess(offset_y + height / 2.5, height / 2)
