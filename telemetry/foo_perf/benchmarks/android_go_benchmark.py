# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import contextlib

from telemetry.core import android_platform
from telemetry.internal.browser import browser_finder
from telemetry.timeline import chrome_trace_category_filter
from telemetry.util import wpr_modes
from telemetry.web_perf import timeline_based_measurement
from telemetry import benchmark
from telemetry import story as story_module

from devil.android.sdk import intent


class SharedAndroidStoryState(story_module.SharedState):

  def __init__(self, test, finder_options, story_set):
    """
    Args:
      test: (unused)
      finder_options: A finder_options object
      story_set: (unused)
    """
    super(SharedAndroidStoryState, self).__init__(
        test, finder_options, story_set)
    self._possible_browser = browser_finder.FindBrowser(finder_options)
    self._finder_options = finder_options
    self._current_story = None

    assert isinstance(self.platform, android_platform.AndroidPlatform)

    # TODO: Use options to configure network_controller properly.
    self.platform.network_controller.Open(wpr_modes.WPR_OFF)
    self.platform.Initialize()

  def TearDownState(self):
    self.platform.network_controller.Close()

  @property
  def platform(self):
    return self._possible_browser.platform

  @property
  def possible_browser(self):
    return self._possible_browser

  @contextlib.contextmanager
  def BrowserEnvironment(self):
    try:
      self._possible_browser.SetUpEnvironment(
          self._finder_options.browser_options)
      yield
    finally:
      self._possible_browser.CleanUpEnvironment()

  @contextlib.contextmanager
  def FindBrowser(self):
    browser = self._possible_browser.Create(find_existing=True)
    try:
      yield
    finally:
      browser.Close()

  def LaunchBrowser(self, url):
    # TODO: Reconsider where this method belongs, and which arguments should
    # it receive.
    # TODO: Android Go stories would, e.g. use the customtabs helper app to
    # launch Chrome as a custom tab.
    # TODO: We shouldn't need to access all those private attributes.
    browser_settings = self._possible_browser._backend_settings
    self.platform._platform_backend.device.StartActivity(
        intent.Intent(package=browser_settings.package,
                      activity=browser_settings.activity,
                      action=None, data=url, category=None, extras=None),
        blocking=True)

  def WillRunStory(self, story):
    self._current_story = story

  def RunStory(self, _):
    self._current_story.Run(self)

  def DidRunStory(self, _):
    self._current_story = None

  def DumpStateUponFailure(self, _story, _results):
    ## TODO: How can this dump failure state from the browser??
    pass

  def CanRunStory(self, _):
    return True


class AndroidGoFooStory(story_module.Story):
  def __init__(self):
    super(AndroidGoFooStory, self).__init__(
        SharedAndroidStoryState, name='foo:bar:baz')

  def Run(self, state):
    with state.BrowserEnvironment():
      state.LaunchBrowser('https://en.wikipedia.org/wiki/Main_Page')
      with state.FindBrowser() as browser:
        action_runner = browser.foreground_tab.action_runner
        action_runner.tab.WaitForDocumentReadyStateToBeComplete()
        action_runner.RepeatableBrowserDrivenScroll(repeat_count=2)


class AndroidGoStories(story_module.StorySet):
  def __init__(self):
    super(AndroidGoStories, self).__init__()
    self.AddStory(AndroidGoFooStory())


class AndroidGoBenchmark(benchmark.Benchmark):
  def CreateCoreTimelineBasedMeasurementOptions(self):
    cat_filter = chrome_trace_category_filter.ChromeTraceCategoryFilter(
        filter_string='rail,toplevel')

    options = timeline_based_measurement.Options(cat_filter)
    options.config.enable_chrome_trace = True
    options.SetTimelineBasedMetrics([
        'clockSyncLatencyMetric',
        'tracingMetric',
    ])
    return options

  def CreateStorySet(self, options):
    return AndroidGoStories()

  @classmethod
  def Name(cls):
    return 'android_go.example'
