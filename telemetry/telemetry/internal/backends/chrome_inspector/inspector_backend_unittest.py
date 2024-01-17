# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from telemetry import decorators
from telemetry.core import exceptions
from telemetry.testing import browser_test_case
from telemetry.testing import tab_test_case

import py_utils


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

  def testWaitForSharedStorageEventsStrict_Passes(self):
    self._tab.Navigate(self.UrlOfUnittestFile('blank.html'))
    context_map = self._devtools_client.GetUpdatedInspectableContexts()
    backend = context_map.GetInspectorBackend(context_map.contexts[0]['id'])
    enabled = backend.EvaluateJavaScript('Boolean(window.sharedStorage)')
    if not enabled:
      raise RuntimeError("Shared Storage not enabled")
    backend.EnableSharedStorageNotifications()
    self.assertTrue(backend.shared_storage_notifications_enabled)
    backend.EvaluateJavaScript("window.sharedStorage.set('a', 'b')",
                               promise=True)
    backend.EvaluateJavaScript("window.sharedStorage.append('c', 'd')",
                               promise=True)
    backend.EvaluateJavaScript("window.sharedStorage.delete('a')",
                               promise=True)
    expected_events = [{'type': 'documentSet',
                        'params': {'key': 'a', 'value': 'b'}},
                       {'type': 'documentAppend',
                        'params': {'key': 'c', 'value': 'd'}},
                       {'type': 'documentDelete'}]
    backend.WaitForSharedStorageEvents(expected_events, mode='strict')
    backend.DisableSharedStorageNotifications()
    self.assertFalse(backend.shared_storage_notifications_enabled)
    backend.ClearSharedStorageNotifications()

  def testWaitForSharedStorageEventsStrict_Fails(self):
    self._tab.Navigate(self.UrlOfUnittestFile('blank.html'))
    context_map = self._devtools_client.GetUpdatedInspectableContexts()
    backend = context_map.GetInspectorBackend(context_map.contexts[0]['id'])
    enabled = backend.EvaluateJavaScript('Boolean(window.sharedStorage)')
    if not enabled:
      raise RuntimeError("Shared Storage not enabled")
    backend.EnableSharedStorageNotifications()
    self.assertTrue(backend.shared_storage_notifications_enabled)
    backend.EvaluateJavaScript("window.sharedStorage.set('a', 'b')",
                               promise=True)
    backend.EvaluateJavaScript("window.sharedStorage.delete('a')",
                               promise=True)
    expected_events = [{'type': 'documentDelete'},
                       {'type': 'documentSet',
                        'params': {'key': 'a', 'value': 'b'}}]
    with self.assertRaises(py_utils.TimeoutException):
      backend.WaitForSharedStorageEvents(expected_events, mode='strict',
                                         timeout=10)
    backend.DisableSharedStorageNotifications()
    self.assertFalse(backend.shared_storage_notifications_enabled)
    backend.ClearSharedStorageNotifications()

  def testWaitForSharedStorageEventsRelaxed_Passes(self):
    self._tab.Navigate(self.UrlOfUnittestFile('blank.html'))
    context_map = self._devtools_client.GetUpdatedInspectableContexts()
    backend = context_map.GetInspectorBackend(context_map.contexts[0]['id'])
    enabled = backend.EvaluateJavaScript('Boolean(window.sharedStorage)')
    if not enabled:
      raise RuntimeError("Shared Storage not enabled")
    backend.EnableSharedStorageNotifications()
    self.assertTrue(backend.shared_storage_notifications_enabled)
    backend.EvaluateJavaScript("window.sharedStorage.set('a', 'b')",
                               promise=True)
    backend.EvaluateJavaScript("window.sharedStorage.append('c', 'd')",
                               promise=True)
    backend.EvaluateJavaScript("window.sharedStorage.delete('a')",
                               promise=True)
    expected_events = [{'type': 'documentAppend'},
                       {'type': 'documentDelete',
                        'params': {'key': 'a'}}]
    backend.WaitForSharedStorageEvents(expected_events, mode='relaxed')
    backend.DisableSharedStorageNotifications()
    self.assertFalse(backend.shared_storage_notifications_enabled)
    backend.ClearSharedStorageNotifications()

  def testWaitForSharedStorageEventsRelaxed_Fails(self):
    self._tab.Navigate(self.UrlOfUnittestFile('blank.html'))
    context_map = self._devtools_client.GetUpdatedInspectableContexts()
    backend = context_map.GetInspectorBackend(context_map.contexts[0]['id'])
    enabled = backend.EvaluateJavaScript('Boolean(window.sharedStorage)')
    if not enabled:
      raise RuntimeError("Shared Storage not enabled")
    backend.EnableSharedStorageNotifications()
    self.assertTrue(backend.shared_storage_notifications_enabled)
    backend.EvaluateJavaScript("window.sharedStorage.set('a', 'b')",
                               promise=True)
    backend.EvaluateJavaScript("window.sharedStorage.delete('a')",
                               promise=True)
    expected_events = [{'type': 'documentSet',
                        'params': {'key': 'a', 'value': 'b'}},
                       {'type': 'documentDelete',
                        'params': {'key': 'c'}}]
    with self.assertRaises(py_utils.TimeoutException):
      backend.WaitForSharedStorageEvents(expected_events, mode='relaxed',
                                         timeout=10)
    backend.DisableSharedStorageNotifications()
    self.assertFalse(backend.shared_storage_notifications_enabled)
    backend.ClearSharedStorageNotifications()
