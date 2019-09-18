# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys
import py_utils

from telemetry.internal.actions.key_event import KeyPressAction


class DevTools(object):

  def __init__(self, tab_inspector_backend, url):
    self._tab_inspector_backend = tab_inspector_backend
    self._tab_url = url
    self._inspector_backend = None

  def WaitForConnectionState(self, connection_state, timeout=6000):
    """Wait for a tab's devtools connection to match the given connection state

    # waits for the devtools to be connected
    Example: devtools.WaitForConnectionState(true)

    # waits for the devtools to be disconnected
    # Example: devtools.WaitForConnectionState(false)

    args:
    connection_state: bool indicating if wait is for devtools to be connected or
    disconnected

    Optional args:
      timeout: The number in seconds to wait for the connection (default to 60).

    Raises:
      py_utils.TimeoutException
      exceptions.EvaluationException
      exceptions.WebSocketException
      exceptions.DevtoolsTargetCrashException
    """

    def HasReachedConnectionState():
      self._inspector_backend = \
          self._tab_inspector_backend.GetDevToolsInspectorBackend(self._tab_url)
      is_connected = self._inspector_backend is not None
      return is_connected == connection_state

    try:
      py_utils.WaitFor(HasReachedConnectionState, timeout)
    except py_utils.TimeoutException as e:
      # Try to make timeouts a little more actionable by dumping console output.
      debug_message = None
      try:
        debug_message = (
            'Console output:\n%s' %
            self._tab_inspector_backend.GetCurrentConsoleOutputBuffer())
      except Exception as e: # pylint: disable=broad-except
        debug_message = (
            'Exception thrown when trying to capture console output: %s' %
            repr(e))
      # Rethrow with the original stack trace for better debugging.
      raise py_utils.TimeoutException, \
          py_utils.TimeoutException(
              'Timeout after %ss while waiting for DevTools connection:'
              % timeout + self._tab_url + '\n' +  e.message + '\n' +\
              debug_message), \
          sys.exc_info()[2]

  def ExecuteJavaScript(self, *args, **kwargs):
    """Executes a given JavaScript statement. Does not return the result.

    Example: devtools.ExecuteJavaScript('var foo = {{ @value }};', value='hi');

    Args:
      statement: The statement to execute (provided as a string).

    Optional keyword args:
      timeout: The number of seconds to wait for the statement to execute.
      context_id: The id of an iframe where to execute the code; the main page
          has context_id=1, the first iframe context_id=2, etc.
      user_gesture: Whether execution should be treated as initiated by user
          in the UI. Code that plays media or requests fullscreen may not take
          effects without user_gesture set to True.
      Additional keyword arguments provide values to be interpolated within
          the statement. See telemetry.util.js_template for details.

    Raises:
      py_utils.TimeoutException
      exceptions.EvaluationException
      exceptions.WebSocketException
      exceptions.DevtoolsTargetCrashException
    """
    return self._inspector_backend.ExecuteJavaScript(*args, **kwargs)

  def EvaluateJavaScript(self, expression, **kwargs):
    """Returns the result of evaluating a given JavaScript expression.

    Example: devtools.ExecuteJavaScript('document.location.href');

    Args:
      expression: The expression to execute (provided as a string).

    Optional keyword args:
      timeout: The number of seconds to wait for the expression to evaluate.
      context_id: The id of an iframe where to execute the code; the main page
          has context_id=1, the first iframe context_id=2, etc.
      user_gesture: Whether execution should be treated as initiated by user
          in the UI. Code that plays media or requests fullscreen may not take
          effects without user_gesture set to True.
      Additional keyword arguments provide values to be interpolated within
          the expression. See telemetry.util.js_template for details.

    Raises:
      py_utils.TimeoutException
      exceptions.EvaluationException
      exceptions.WebSocketException
      exceptions.DevtoolsTargetCrashException
    """
    return self._inspector_backend.EvaluateJavaScript(expression, **kwargs)

  def ShowPanel(self, panel_name):
    """Switches to the specified tool panel

    Example: devtools.ShowPanel('console');

    Args:
      panel_name: The name of the tool panel to show (provided as a string).

    Raises:
      py_utils.TimeoutException
      exceptions.EvaluationException
      exceptions.WebSocketException
      exceptions.DevtoolsTargetCrashException
    """

    return self.ExecuteJavaScript("""
        (function() {
          UI.inspectorView.showPanel('{{ @panel_name }}');
        })();
        """, panel_name=panel_name)

  def WaitForJavaScriptCondition(self, condition, **kwargs):
    """Wait for a JavaScript condition to become truthy.

    Example: runner.WaitForJavaScriptCondition('window.foo == 10');

    Args:
      condition: The JavaScript condition (provided as string).

    Optional keyword args:
      timeout: The number in seconds to wait for the condition to become
          True (default to 60).
      context_id: The id of an iframe where to execute the code; the main page
          has context_id=1, the first iframe context_id=2, etc.
      Additional keyword arguments provide values to be interpolated within
          the expression. See telemetry.util.js_template for details.

    Returns:
      The value returned by the JavaScript condition that got interpreted as
      true.

    Raises:
      py_utils.TimeoutException
      exceptions.EvaluationException
      exceptions.WebSocketException
      exceptions.DevtoolsTargetCrashException
    """
    return self._inspector_backend.WaitForJavaScriptCondition(condition,
                                                              **kwargs)

  def WaitForPerformanceMark(self, perf_mark, min_mark_count=1, timeout=60):
    """ Wait for a performance mark of the given name to occur in the devtools
        frontend. Marks occur when performance.mark(...) is called.

    Args:
      perf_mark: Name of mark to wait for
      min_mark_count: Causes this function to wait for at
          least <min_mark_count> occurences of perf_mark. By default, this
          function will wait for only one occurence.
    """
    self.WaitForJavaScriptCondition("""
        performance.getEntriesByName('{{ @mark }}').length >= {{ @min_count }}
        """, mark=perf_mark, min_count=str(min_mark_count), timeout=timeout)

  def EnterAsciiText(self, text, timeout=60):
    """Sends key press events for each character in text

    Args:
      text: String to be entered as key press events
    """
    for char in text:
      self.PressKey(char, timeout=timeout)

  def PressKey(self, key, timeout=60, use_native_key=False):
    """Perform a key press.

    Args:
      key: DOM value of the pressed key (e.g. 'PageDown', see
          https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key).
    """

    action = KeyPressAction(key, timeout=timeout, use_native_key=use_native_key)
    action.RunAction(self)

  def DispatchKeyEvent(self, key_event_type='char', modifiers=None,
                       timestamp=None, text=None, unmodified_text=None,
                       key_identifier=None, dom_code=None, dom_key=None,
                       windows_virtual_key_code=None,
                       native_virtual_key_code=None, auto_repeat=None,
                       is_keypad=None, is_system_key=None, timeout=60):
    """Dispatches a key event to the page.

    Args:
      type: Type of the key event. Allowed values: 'keyDown', 'keyUp',
          'rawKeyDown', 'char'.
      modifiers: Bit field representing pressed modifier keys. Alt=1, Ctrl=2,
          Meta/Command=4, Shift=8 (default: 0).
      timestamp: Time at which the event occurred. Measured in UTC time in
          seconds since January 1, 1970 (default: current time).
      text: Text as generated by processing a virtual key code with a keyboard
          layout. Not needed for for keyUp and rawKeyDown events (default: '').
      unmodified_text: Text that would have been generated by the keyboard if no
          modifiers were pressed (except for shift). Useful for shortcut
          (accelerator) key handling (default: "").
      key_identifier: Unique key identifier (e.g., 'U+0041') (default: '').
      windows_virtual_key_code: Windows virtual key code (default: 0).
      native_virtual_key_code: Native virtual key code (default: 0).
      auto_repeat: Whether the event was generated from auto repeat (default:
          False).
      is_keypad: Whether the event was generated from the keypad (default:
          False).
      is_system_key: Whether the event was a system key event (default: False).

    Raises:
      py_utils.TimeoutException
      exceptions.DevtoolsTargetCrashException
    """
    return self._inspector_backend.DispatchKeyEvent(
        key_event_type=key_event_type, modifiers=modifiers, timestamp=timestamp,
        text=text, unmodified_text=unmodified_text,
        key_identifier=key_identifier, dom_code=dom_code, dom_key=dom_key,
        windows_virtual_key_code=windows_virtual_key_code,
        native_virtual_key_code=native_virtual_key_code,
        auto_repeat=auto_repeat, is_keypad=is_keypad,
        is_system_key=is_system_key, timeout=timeout)

