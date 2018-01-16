# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import logging
import os
import shutil
import tempfile
import unittest

from telemetry.core import util
from telemetry import decorators
from telemetry.internal.browser import browser_finder
from telemetry.internal.browser import extension_to_load
from telemetry.testing import options_for_unittests


class ExtensionTest(unittest.TestCase):
  @contextlib.contextmanager
  def BrowserWithExtension(self, ext_path):
    extension_path = os.path.join(util.GetUnittestDataDir(), ext_path)
    options = options_for_unittests.GetCopy()
    load_extension = extension_to_load.ExtensionToLoad(
        extension_path, options.browser_type)
    options.browser_options.extensions_to_load = [load_extension]
    browser_to_create = browser_finder.FindBrowser(options)

    if not browser_to_create:
      self.skipTest("Did not find a browser that supports extensions")

    platform = browser_to_create.platform
    try:
      platform.network_controller.Open()
      with browser_to_create.BrowserSession(
          options.browser_options) as browser:
        extension = browser.extensions[load_extension]
        self.assertTrue(extension)
        self.assertEqual(extension.extension_id, load_extension.extension_id)
        yield browser, extension
    finally:
      platform.network_controller.Close()

  def testExtensionBasic(self):
    """Test ExtensionPage's ExecuteJavaScript and EvaluateJavaScript."""
    with self.BrowserWithExtension('simple_extension') as (_, extension):
      self.assertTrue(
          extension.EvaluateJavaScript('chrome.runtime != null'))
      extension.ExecuteJavaScript('setTestVar("abcdef")')
      self.assertEquals('abcdef',
                        extension.EvaluateJavaScript('_testVar'))

  def testExtensionGetByExtensionId(self):
    """Test GetByExtensionId for a simple extension with a background page."""
    with self.BrowserWithExtension('simple_extension') as (browser, extension):
      extensions = browser.extensions.GetByExtensionId(extension.extension_id)
      self.assertEqual(1, len(extensions))
      self.assertEqual(extensions[0], extension)
      self.assertTrue(
          extensions[0].EvaluateJavaScript('chrome.runtime != null'))

  @decorators.Disabled('mac')
  def testWebApp(self):
    """Tests GetByExtensionId for a web app with multiple pages."""
    with self.BrowserWithExtension('simple_app') as (browser, extension):
      extensions = browser.extensions.GetByExtensionId(extension.extension_id)
      extension_urls = set([ext.EvaluateJavaScript('location.href;')
                            for ext in extensions])
      expected_urls = set([
          'chrome-extension://' + extension.extension_id + '/' + path
          for path in ['main.html', 'second.html',
                       '_generated_background_page.html']])
      self.assertEqual(expected_urls, extension_urls)

class NonExistentExtensionTest(unittest.TestCase):
  def testNonExistentExtensionPath(self):
    """Test that a non-existent extension path will raise an exception."""
    extension_path = os.path.join(util.GetUnittestDataDir(), 'foo')
    options = options_for_unittests.GetCopy()
    self.assertRaises(extension_to_load.ExtensionPathNonExistentException,
                      lambda: extension_to_load.ExtensionToLoad(
                          extension_path, options.browser_type))

  def testExtensionNotLoaded(self):
    """Querying an extension that was not loaded will return None"""
    extension_path = os.path.join(util.GetUnittestDataDir(), 'simple_extension')
    options = options_for_unittests.GetCopy()
    load_extension = extension_to_load.ExtensionToLoad(
        extension_path, options.browser_type)
    browser_to_create = browser_finder.FindBrowser(options)
    try:
      browser_to_create.platform.network_controller.Open()
      with browser_to_create.Create(options) as b:
        if b.supports_extensions:
          self.assertRaises(KeyError, lambda: b.extensions[load_extension])
    finally:
      browser_to_create.platform.network_controller.Close()

class MultipleExtensionTest(unittest.TestCase):
  def setUp(self):
    """ Copy the manifest and background.js files of simple_extension to a
    number of temporary directories to load as extensions"""
    self._extension_dirs = [tempfile.mkdtemp() for _ in range(3)]
    src_extension_dir = os.path.join(
        util.GetUnittestDataDir(), 'simple_extension')
    manifest_path = os.path.join(src_extension_dir, 'manifest.json')
    script_path = os.path.join(src_extension_dir, 'background.js')
    for d in self._extension_dirs:
      shutil.copy(manifest_path, d)
      shutil.copy(script_path, d)
    options = options_for_unittests.GetCopy()
    self._extensions_to_load = [
        extension_to_load.ExtensionToLoad(d, options.browser_type)
        for d in self._extension_dirs
    ]
    options.browser_options.extensions_to_load = self._extensions_to_load
    browser_to_create = browser_finder.FindBrowser(options)
    self._platform = None
    self._browser = None
    # May not find a browser that supports extensions.
    if browser_to_create:
      self._platform = browser_to_create.platform
      self._platform.network_controller.Open()
      self._browser = browser_to_create.Create(options)

  def tearDown(self):
    if self._platform:
      self._platform.network_controller.Close()
    if self._browser:
      self._browser.Close()
    for d in self._extension_dirs:
      shutil.rmtree(d)

  def testMultipleExtensions(self):
    if not self._browser:
      logging.warning('Did not find a browser that supports extensions, '
                      'skipping test.')
      return

    # Test contains.
    loaded_extensions = [e for e in self._extensions_to_load
                         if e in self._browser.extensions]
    self.assertEqual(len(loaded_extensions), len(self._extensions_to_load))
    for load_extension in self._extensions_to_load:
      extension = self._browser.extensions[load_extension]
      assert extension
      self.assertTrue(
          extension.EvaluateJavaScript('chrome.runtime != null'))
      extension.ExecuteJavaScript('setTestVar("abcdef")')
      self.assertEquals('abcdef', extension.EvaluateJavaScript('_testVar'))


class WebviewInExtensionTest(ExtensionTest):

  # Flaky on windows, hits an exception: http://crbug.com/508325
  # Flaky on macOS too: http://crbug.com/661434
  # ChromeOS: http://crbug.com/674220
  @decorators.Disabled('win', 'linux', 'mac', 'chromeos')
  def testWebviewInExtension(self):
    """Tests GetWebviewContext() for a web app containing <webview> element."""
    with self.BrowserWithExtension('webview_app') as (_, extension):
      webview_contexts = extension.GetWebviewContexts()
      self.assertEquals(1, len(webview_contexts))
      webview_context = webview_contexts[0]
      webview_context.WaitForDocumentReadyStateToBeComplete()
      # Check that the context has the right url from the <webview> element.
      self.assertTrue(webview_context.GetUrl().startswith('data:'))
      # Check |test_input_id| element is accessible from the webview context.
      self.assertTrue(
          webview_context.EvaluateJavaScript(
              'document.getElementById("test_input_id") != null'))
      # Check that |test_input_id| is not accessible from outside of the
      # webview context.
      self.assertFalse(
          extension.EvaluateJavaScript(
              'document.getElementById("test_input_id") != null'))
