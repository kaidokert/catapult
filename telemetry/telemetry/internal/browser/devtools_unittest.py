# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from telemetry import decorators
from telemetry.testing import tab_test_case


class DevToolsTest(tab_test_case.TabTestCase):
  @property
  def _browser_backend(self):
    return self._browser._browser_backend

  @property
  def _devtools_client(self):
    return self._browser_backend.devtools_client

  # https://github.com/catapult-project/catapult/issues/3099 (Android)
  # crbug.com/483212 (CrOS)
  @decorators.Enabled('has tabs')
  @decorators.Disabled('android', 'chromeos')
  def testOpenAndCloseDevTools(self):
    self._tab.OpenDevTools()
    self.assertTrue(self._tab.devtools is not None)
    self._tab.CloseDevTools()
    self.assertTrue(self._tab.devtools is None)

  # https://github.com/catapult-project/catapult/issues/3099 (Android)
  # crbug.com/483212 (CrOS)
  @decorators.Enabled('has tabs')
  @decorators.Disabled('android', 'chromeos')
  def testOpenAndCloseDevToolsAgainstBlank(self):
    url = self.UrlOfUnittestFile('blank.html')
    self._tab.Navigate(url)
    self._tab.OpenDevTools()
    self.assertTrue(self._tab.devtools is not None)
    self._tab.CloseDevTools()
    self.assertTrue(self._tab.devtools is None)

  # https://github.com/catapult-project/catapult/issues/3099 (Android)
  # crbug.com/483212 (CrOS)
  @decorators.Enabled('has tabs')
  @decorators.Disabled('android', 'chromeos')
  def testOpenAndCloseDevToolsAgainstSettings(self):
    self._tab.Navigate('edge://settings')
    self._tab.WaitForDocumentReadyStateToBeComplete()
    self._tab.action_runner.WaitForNetworkQuiescence()
    self._tab.OpenDevTools()
    self.assertTrue(self._tab.devtools is not None)
    self._tab.CloseDevTools()
    self.assertTrue(self._tab.devtools is None)

  # https://github.com/catapult-project/catapult/issues/3099 (Android)
  # crbug.com/483212 (CrOS)
  @decorators.Enabled('has tabs')
  @decorators.Disabled('android', 'chromeos')
  def testShowPanel(self):
    self._tab.OpenDevTools()
    self._tab.devtools.ShowPanel('sources')
    name = self._tab.devtools.EvaluateJavaScript(
        'UI.inspectorView._tabbedPane.selectedTabId')
    self.assertEqual(name, 'sources')
