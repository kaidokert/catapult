# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""A Telemetry page_action that opens a popup with given URL from this tab.

Action parameters are:
- target_url: The URL for the popup window.
- timeout: Number of seconds to pause for the window to reach
           document.readyState "complete" (all content received).
"""
from telemetry.core import exceptions
from telemetry.internal.actions import page_action

class NewWindowAction(page_action.PageAction):

  def __init__(self, target_url, timeout):
    super(NewWindowAction, self).__init__(timeout=timeout)
    self.target_url = target_url

  def RunAction(self, tab):
    new_window_cmd = "window.open('" + self.target_url + "','', 'location=yes')"
    try:
      tab.ExecuteJavaScript(new_window_cmd)
      tab.WaitForJavaScriptCondition("document.readyState == 'complete'",
                                     timeout=self.timeout)
    except exceptions.EvaluateException:
      raise RuntimeError("Could not open window with url %s" % self.target_url)

  def __str__(self):
    return "%s('%s')" % (self.__class__.__name__, self.target_url)
