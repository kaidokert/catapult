# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

from telemetry.core import exceptions
from telemetry.internal.backends.chrome_inspector import inspector_backend_list
from telemetry.internal.browser import tab

import py_utils


class TabUnexpectedResponseException(exceptions.DevtoolsTargetCrashException):
  pass

class UnsupportedTabTypeException(exceptions.StoryActionError):
  pass


class TabListBackend(inspector_backend_list.InspectorBackendList):
  """A dynamic sequence of tab.Tabs in UI order."""

  def __init__(self, browser_backend):
    super(TabListBackend, self).__init__(browser_backend)

  def New(self, tab_type, timeout):
    """Makes a new tab of specified type.

    Args:
      tab_type: One of TAB_IN_CURRENT_WINDOW or TAB_IN_NEW_POPUP.
      timeout: Seconds to wait for the new tab request to complete.

    Returns:
      A Tab object.

    Raises:
      devtools_http.DevToolsClientConnectionError
      UnsupportedTabTypeException: if the supplied |tab_type| is not known.
      exceptions.EvaluateException: for the current implementation of opening
                                    a tab in a new window.
    """
    if not self._browser_backend.supports_tab_control:
      raise NotImplementedError("Browser doesn't support tab control.")
    if tab_type == "TAB_IN_CURRENT_WINDOW":
      response = self._browser_backend.devtools_client.RequestNewTab(timeout)
      try:
        response = json.loads(response)
        context_id = response['id']
      except (KeyError, ValueError):
        raise TabUnexpectedResponseException(
            app=self._browser_backend.browser,
            msg='Received response: %s' % response)
      return self.GetBackendFromContextId(context_id)
    elif tab_type == "TAB_IN_NEW_POPUP":
      # TODO(crbug.com/943279): Refactor to use DevTools API once that supports
      #                         new window creation.
      new_window_cmd = "window.open('','', 'location=yes')"
      document_complete_condition = "document.readyState == 'complete'"
      open_context_ids = list(self.IterContextIds())
      existing_window = self.GetBackendFromContextId(open_context_ids[0])
      try:
        existing_window.ExecuteJavaScript(new_window_cmd)
        existing_window.WaitForJavaScriptCondition(document_complete_condition,
                                                   timeout=timeout)
        open_context_ids_after_new_window = list(self.IterContextIds())
        new_ids = [tab_id for tab_id in open_context_ids_after_new_window
                   if tab_id not in open_context_ids]
        if len(new_ids) == 1:
          return self.GetBackendFromContextId(new_ids[0])
        raise TabUnexpectedResponseException(
            app=self._browser_backend.browser,
            msg='Unable to determine if a new window was successfully opened')
      except exceptions.EvaluateException:
        raise RuntimeError("Couldn't open window with url %s" % self.target_url)
    else:
      raise UnsupportedTabTypeException(
          msg="tab_type %s is unsupported" % tab_type)

  def CloseTab(self, tab_id, timeout=300):
    """Closes the tab with the given debugger_url.

    Raises:
      devtools_http.DevToolsClientConnectionError
      devtools_client_backend.TabNotFoundError
      TabUnexpectedResponseException
      py_utils.TimeoutException
    """
    assert self._browser_backend.supports_tab_control

    response = self._browser_backend.devtools_client.CloseTab(tab_id, timeout)

    if response != 'Target is closing':
      raise TabUnexpectedResponseException(
          app=self._browser_backend.browser,
          msg='Received response: %s' % response)

    py_utils.WaitFor(lambda: tab_id not in self.IterContextIds(), timeout=5)

  def ActivateTab(self, tab_id, timeout=30):
    """Activates the tab with the given debugger_url.

    Raises:
      devtools_http.DevToolsClientConnectionError
      devtools_client_backend.TabNotFoundError
      TabUnexpectedResponseException
    """
    assert self._browser_backend.supports_tab_control

    response = self._browser_backend.devtools_client.ActivateTab(tab_id,
                                                                 timeout)

    if response != 'Target activated':
      raise TabUnexpectedResponseException(
          app=self._browser_backend.browser,
          msg='Received response: %s' % response)

    # Activate tab call is synchronous, so wait to make sure that Chrome
    # have time to promote this tab to foreground.
    py_utils.WaitFor(
        lambda: tab_id == self._browser_backend.browser.foreground_tab.id,
        timeout=5)

  def Get(self, index, ret):
    """Returns self[index] if it exists, or ret if index is out of bounds."""
    if len(self) <= index:
      return ret
    return self[index]

  def ShouldIncludeContext(self, context):
    if 'type' in context:
      return (context['type'] == 'page' or
              context['url'] == 'chrome://media-router/')
    # TODO: For compatibility with Chrome before r177683.
    # This check is not completely correct, see crbug.com/190592.
    return not context['url'].startswith('chrome-extension://')

  def CreateWrapper(self, inspector_backend):
    return tab.Tab(inspector_backend, self, self._browser_backend.browser)

  def _HandleDevToolsConnectionError(self, error):
    if not self._browser_backend.IsAppRunning():
      error.AddDebuggingMessage('The browser is not running. It probably '
                                'crashed.')
    elif not self._browser_backend.HasDevToolsConnection():
      error.AddDebuggingMessage('The browser exists but cannot be reached.')
    else:
      error.AddDebuggingMessage('The browser exists and can be reached. '
                                'The devtools target probably crashed.')
