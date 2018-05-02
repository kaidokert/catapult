# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib

from telemetry import decorators
from telemetry import page as page_module
from telemetry import story
from telemetry.page import cache_temperature
from telemetry.internal.testing.test_page_sets import example_domain
from telemetry.testing import browser_test_case
from telemetry.timeline import tracing_config
from tracing.trace_data import trace_data


class CacheTemperatureTests(browser_test_case.BrowserTestCase):
  def __init__(self, *args, **kwargs):
    super(CacheTemperatureTests, self).__init__(*args, **kwargs)
    self._full_trace = None
    self._story_set = example_domain.ExampleDomainPageSet()
    self._page = self._story_set.stories[0]

  @contextlib.contextmanager
  def CreateReplayNetworkAndCatpureTrace(self):
    archive_path = self._story_set.WprFilePathForStory(
        self._page, self._browser.platform.GetOSName())
    self._browser.platform.network_controller.StartReplay(archive_path)
    tracing_controller = self._browser.platform.tracing_controller
    options = tracing_config.TracingConfig()
    options.enable_chrome_trace = True
    tracing_controller.StartTracing(options)
    try:
      yield
    finally:
       self._browser.platform.network_controller.StopReplay()
       self._full_trace = tracing_controller.StopTracing()[0]
    self._full_trace.Serialize(
        '/Users/nednguyen/projects/chromium/src/tools/swarming_client/foo/trace.html')


  def traceMarkers(self):
    if not self._full_trace:
      return set()

    chrome_trace = self._full_trace.GetTraceFor(trace_data.CHROME_TRACE_PART)
    return set(
        event['name']
        for event in chrome_trace['traceEvents']
        if event['cat'] == 'blink.console')

  @decorators.Enabled('has tabs')
  def testEnsureAny(self):
    with self.CreateReplayNetworkAndCatpureTrace():
      story_set = example_domain.ExampleDomainPageSet()
      page = story_set.stories[0]
      cache_temperature.EnsurePageCacheTemperature(page, self._browser)

    markers = self.traceMarkers()
    self.assertNotIn('telemetry.internal.ensure_diskcache.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.warm.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.warm.end', markers)
    self.assertNotIn('telemetry.internal.warm_cache.hot.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.hot.end', markers)

  @decorators.Enabled('has tabs')
  @decorators.Disabled('chromeos')
  def testEnsureCold(self):
    with self.CreateReplayNetworkAndCatpureTrace():
      story_set = example_domain.ExampleDomainPageSet()
      cache_temperature.EnsurePageCacheTemperature(page, self._browser)

    markers = self.traceMarkers()
    self.assertIn('telemetry.internal.ensure_diskcache.start', markers)
    self.assertIn('telemetry.internal.ensure_diskcache.end', markers)

  @decorators.Disabled('reference')
  @decorators.Enabled('has tabs')
  def testEnsureWarmAfterColdRun(self):
    with self.CreateReplayNetworkAndCatpureTrace():
      story_set = example_domain.ExampleDomainPageSet()
      page = page_module.Page(
          'http://google.com', page_set=story_set,
          cache_temperature=cache_temperature.COLD, name='http://google.com')
      cache_temperature.EnsurePageCacheTemperature(page, self._browser)

      previous_page = page
      page = page_module.Page(
          'http://google.com', page_set=story_set,
          cache_temperature=cache_temperature.WARM, name='http://google.com')
      cache_temperature.EnsurePageCacheTemperature(
          page, self._browser, previous_page)

    markers = self.traceMarkers()
    self.assertNotIn('telemetry.internal.warm_cache.warm.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.warm.end', markers)
    self.assertNotIn('telemetry.internal.warm_cache.hot.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.hot.end', markers)

  @decorators.Disabled('reference')
  @decorators.Enabled('has tabs')
  @decorators.Disabled('chromeos')
  def testEnsureWarmFromScratch(self):
    with self.CreateReplayNetworkAndCatpureTrace():
      story_set = example_domain.ExampleDomainPageSet()
      page = page_module.Page(
          'http://google.com', page_set=story_set,
          cache_temperature=cache_temperature.WARM, name='http://google.com')
      cache_temperature.EnsurePageCacheTemperature(page, self._browser)

    markers = self.traceMarkers()
    self.assertIn('telemetry.internal.warm_cache.warm.start', markers)
    self.assertIn('telemetry.internal.warm_cache.warm.end', markers)

  @decorators.Disabled('reference')
  @decorators.Enabled('has tabs')
  def testEnsureHotAfterColdAndWarmRun(self):
    with self.CreateReplayNetworkAndCatpureTrace():
      story_set = example_domain.ExampleDomainPageSet()
      page = page_module.Page(
          'http://google.com', page_set=story_set,
          cache_temperature=cache_temperature.COLD, name='http://google.com')
      cache_temperature.EnsurePageCacheTemperature(page, self._browser)

      previous_page = page
      page = page_module.Page(
          'http://google.com', page_set=story_set,
          cache_temperature=cache_temperature.WARM, name='http://google.com')
      cache_temperature.EnsurePageCacheTemperature(
          page, self._browser, previous_page)

      previous_page = page
      page = page_module.Page(
          'http://google.com', page_set=story_set,
          cache_temperature=cache_temperature.HOT, name='http://google.com')
      cache_temperature.EnsurePageCacheTemperature(
          page, self._browser, previous_page)

    markers = self.traceMarkers()
    self.assertNotIn('telemetry.internal.warm_cache.warm.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.warm.end', markers)
    self.assertNotIn('telemetry.internal.warm_cache.hot.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.hot.end', markers)

  @decorators.Disabled('reference')
  def testEnsureHotAfterColdRun(self):
    with self.CreateReplayNetworkAndCatpureTrace():
      story_set = example_domain.ExampleDomainPageSet()
      page = page_module.Page(
          'http://google.com', page_set=story_set,
          cache_temperature=cache_temperature.COLD, name='http://google.com')
      cache_temperature.EnsurePageCacheTemperature(page, self._browser)

      previous_page = page
      page = page_module.Page(
          'http://google.com', page_set=story_set,
          cache_temperature=cache_temperature.HOT, name='http://google.com')
      cache_temperature.EnsurePageCacheTemperature(
          page, self._browser, previous_page)

    markers = self.traceMarkers()
    # After navigation for another origin url, traces in previous origin page
    # does not appear in |markers|, so we can not check this:
    # self.assertIn('telemetry.internal.warm_cache.hot.start', markers)
    # TODO: Ensure all traces are in |markers|
    self.assertIn('telemetry.internal.warm_cache.hot.end', markers)

  @decorators.Disabled('reference')
  @decorators.Enabled('has tabs')
  @decorators.Disabled('chromeos')
  def testEnsureHotFromScratch(self):
    with self.CreateReplayNetworkAndCatpureTrace():
      cache_temperature.EnsurePageCacheTemperature(self._page, self._browser)

    markers = self.traceMarkers()
    self.assertIn('telemetry.internal.warm_cache.warm.start', markers)
    self.assertIn('telemetry.internal.warm_cache.warm.end', markers)
    self.assertIn('telemetry.internal.warm_cache.hot.start', markers)
    self.assertIn('telemetry.internal.warm_cache.hot.end', markers)

  @decorators.Disabled('reference')
  @decorators.Enabled('has tabs')
  def testEnsureWarmBrowser(self):
    with self.CreateReplayNetworkAndCatpureTrace():
      story_set = example_domain.ExampleDomainPageSet()
      page = page_module.Page(
          'http://google.com', page_set=story_set,
          cache_temperature=cache_temperature.WARM_BROWSER,
          name='http://google.com')
      cache_temperature.EnsurePageCacheTemperature(
          page, self._browser)

    markers = self.traceMarkers()
    # Browser cache warming happens in a different tab so markers shouldn't
    # appear.
    self.assertNotIn('telemetry.internal.warm_cache.warm.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.warm.end', markers)
    self.assertNotIn('telemetry.internal.warm_cache.hot.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.hot.end', markers)

  @decorators.Disabled('reference')
  @decorators.Enabled('has tabs')
  def testEnsureHotBrowser(self):
    with self.CreateReplayNetworkAndCatpureTrace():
      story_set = example_domain.ExampleDomainPageSet()
      page = page_module.Page(
          'http://google.com', page_set=story_set,
          cache_temperature=cache_temperature.HOT_BROWSER,
          name='http://google.com')
      cache_temperature.EnsurePageCacheTemperature(
          page, self._browser)

    markers = self.traceMarkers()
    # Browser cache warming happens in a different tab so markers shouldn't
    # appear.
    self.assertNotIn('telemetry.internal.warm_cache.warm.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.warm.end', markers)
    self.assertNotIn('telemetry.internal.warm_cache.hot.start', markers)
    self.assertNotIn('telemetry.internal.warm_cache.hot.end', markers)
