# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import time

from telemetry import decorators
from telemetry.internal.actions import key_event
from telemetry.internal.actions import utils
from telemetry.testing import tab_test_case


class KeyPressActionTest(tab_test_case.TabTestCase):

  @property
  def _scroll_position(self):
    return self._tab.EvaluateJavaScript(
        'document.documentElement.scrollTop || document.body.scrollTop')

  @property
  def _window_height(self):
    return self._tab.EvaluateJavaScript('__GestureCommon_GetWindowHeight()')

  def _press_key(self, key, modifiers=None):
    action = key_event.KeyPressAction(key, modifiers=modifiers)
    action.WillRunAction(self._tab)
    action.RunAction(self._tab)

  def setUp(self):
    tab_test_case.TabTestCase.setUp(self)
    self.Navigate('blank.html')
    utils.InjectJavaScript(self._tab, 'gesture_common.js')

  # https://github.com/catapult-project/catapult/issues/3099
  # crbug.com/1005062
  @decorators.Disabled('android', 'chromeos')
  def testPressEndAndHome(self):
    # Make page taller than the window so it's scrollable.
    self._tab.ExecuteJavaScript(
        'document.body.style.height ='
        '(3 * __GestureCommon_GetWindowHeight() + 1) + "px";')

    # Check that the browser is currently showing the top of the page and that
    # the page has non-trivial height.
    self.assertEquals(0, self._scroll_position)
    self.assertLess(50, self._window_height)

    self._press_key('End')

    # Scroll happens *after* key press returns, so we need to wait a little.
    time.sleep(1)

    # We can only expect the bottom scroll position to be approximatly equal.
    self.assertAlmostEqual(
        2 * self._window_height, self._scroll_position, delta=20)

    self._press_key('Home')

    # Scroll happens *after* key press returns, so we need to wait a little.
    time.sleep(1)

    self.assertEquals(self._scroll_position, 0)

  def testTextEntry(self):
    # Add an input box to the page.
    self._tab.ExecuteJavaScript(
        '(function() {'
        '  var elem = document.createElement("textarea");'
        '  document.body.appendChild(elem);'
        '  elem.focus();'
        '})();')

    # Simulate typing a sentence.
    for char in 'Hello, World!':
      self._press_key(char)

    # Make changes to the sentence using special keys.
    for _ in xrange(6):
      self._press_key('ArrowLeft')
    self._press_key('Backspace')
    self._press_key('Return')

    # Check that the contents of the textarea is correct. It might take a second
    # until all keystrokes have been handled by the browser (crbug.com/630017).
    self._tab.WaitForJavaScriptCondition(
        'document.querySelector("textarea").value === "Hello,\\nWorld!"',
        timeout=1)

  def testModifierKey(self):
    # Add an input box to the page.
    self._tab.ExecuteJavaScript(
        '(function() {'
        '  var elem = document.createElement("textarea");'
        '  document.body.appendChild(elem);'
        '  elem.focus();'
        '})();')

    # Simulate typing a sentence.
    for char in 'Hello, World!':
      self._press_key(char)

    control = key_event.encode_modifiers(control=True)
    command = key_event.encode_modifiers(meta=True)
    platform = self._tab.browser.platform.GetOSName()
    modifiers = control if platform != 'mac' else command

    # <Ctrl-A> select everything inside input box.
    self._press_key('a', modifiers=modifiers)
    self._press_key('Backspace')
    self._press_key('X')
    # Check that the contents of the textarea is correct. It might take a second
    # until all keystrokes have been handled by the browser (crbug.com/630017).
    self._tab.WaitForJavaScriptCondition(
        'document.querySelector("textarea").value === "X"',
        timeout=1)

  def testPressUnknownKey(self):
    with self.assertRaises(ValueError):
      self._press_key('UnknownKeyName')
