# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from telemetry.testing import browser_test_case


class TabTestCase(browser_test_case.BrowserTestCase):
  def __init__(self, *args):
    super(TabTestCase, self).__init__(*args)
    self._tab = None

  def setUp(self):
    super(TabTestCase, self).setUp()
    assert self._browser.supports_tab_control
    self._tab = self._browser.tabs.New()

  def Navigate(self,
               filename,
               script_to_evaluate_on_commit=None,
               handler_class=None):
    """Navigates |tab| to |filename| in the unittest data directory.

    Also sets up http server to point to the unittest data directory.
    """
    url = self.UrlOfUnittestFile(filename, handler_class)
    self._tab.Navigate(url, script_to_evaluate_on_commit)
    self._tab.WaitForDocumentReadyStateToBeComplete()
    self._tab.WaitForFrameToBeDisplayed()

  @property
  def tabs(self):
    return self._browser.tabs
