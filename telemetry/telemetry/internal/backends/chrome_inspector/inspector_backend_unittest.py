# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from telemetry import decorators
from telemetry.core import exceptions
from telemetry.testing import browser_test_case
from telemetry.testing import tab_test_case


class InspectorBackendTest(browser_test_case.BrowserTestCase):
  @property
  def _devtools_client(self):
    return self._browser._browser_backend.devtools_client

  # https://github.com/catapult-project/catapult/issues/3099 (Android)
  # crbug.com/483212 (CrOS)
  @decorators.Disabled('android', 'chromeos')
  def testWaitForJavaScriptCondition(self):
    context_map = self._devtools_client.GetUpdatedInspectableContexts()
    backend = context_map.GetInspectorBackend(context_map.contexts[0]['id'])
    backend.WaitForJavaScriptCondition('true')

  # https://github.com/catapult-project/catapult/issues/3099 (Android)
  # crbug.com/483212 (CrOS)
  @decorators.Disabled('android', 'chromeos')
  def testWaitForJavaScriptConditionPropagatesEvaluateException(self):
    context_map = self._devtools_client.GetUpdatedInspectableContexts()
    backend = context_map.GetInspectorBackend(context_map.contexts[0]['id'])
    with self.assertRaises(exceptions.EvaluateException):
      backend.WaitForJavaScriptCondition('syntax error!')


class InspectorBackendSharedStorageTest(tab_test_case.TabTestCase):
  @classmethod
  def CustomizeBrowserOptions(cls, options):
    options.AppendExtraBrowserArgs([
      '--enable-features=SharedStorageAPI,'
      + 'FencedFrames:implementation_type/mparch,FencedFramesDefaultMode,'
      + 'PrivacySandboxAdsAPIsOverride,DefaultAllowPrivacySandboxAttestations',
      '--enable-privacy-sandbox-ads-apis'
    ])

  @property
  def _devtools_client(self):
    return self._browser._browser_backend.devtools_client

  def testWaitForSharedStorageEventsStrict(self):
    self._tab.Navigate(self.UrlOfUnittestFile('blank.html'))
    context_map = self._devtools_client.GetUpdatedInspectableContexts()
    backend = context_map.GetInspectorBackend(context_map.contexts[0]['id'])
    enabled = backend.EvaluateJavaScript('Boolean(window.sharedStorage)')
    if not enabled:
      raise RuntimeError("Shared Storage not enabled")
    backend.EnableSharedStorageNotifications()
    backend.EvaluateJavaScript("window.sharedStorage.set('a', 'b')",
                               promise=True)
    expected_events = [{'type': 'documentSet',
                        'params': {'key': 'a', 'value': 'b'}}]
    backend.WaitForSharedStorageEvents(expected_events, mode='strict')
    backend.DisableSharedStorageNotifications()
    backend.ClearSharedStorageNotifications()
