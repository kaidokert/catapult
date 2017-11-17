# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from telemetry.core import android_platform
from telemetry import benchmark
from telemetry import story as story_module
from telemetry.internal.actions import action_runner as action_runner_module
from telemetry.timeline import chrome_trace_category_filter
from telemetry.web_perf import timeline_based_measurement
from telemetry.internal.browser import browser_finder
from telemetry.util import wpr_modes

from devil.android.sdk import intent

class SharedAndroidStoryState(story_module.SharedState):

  def __init__(self, test, options, story_set):
    """
    Args:
      test: (unused)
      options: A finder_options object
      story_set: A story set!
    """
    super(SharedAndroidStoryState, self).__init__(test, options, story_set)
    self._possible_browser = browser_finder.FindBrowser(options)
    self._options = options  # TODO: Avoid keeping these.
    self._current_story = None
    self._browser = None

    #options.browser_options.dont_override_profile = True
    assert isinstance(self.platform, android_platform.AndroidPlatform)

    self.platform.network_controller.InitializeIfNeeded(use_live_traffic=True)
    self.platform.network_controller.Open(wpr_modes.WPR_OFF, [])
    self.platform.Initialize()

  def TearDownState(self):
    self.platform.network_controller.Close()

  @property
  def platform(self):
    return self._possible_browser.platform

  @property
  def browser(self):
    return self._browser

  def WillRunStory(self, story):
    # This should be True on TBM benchmarks.
    assert self.platform.tracing_controller.is_tracing_running
    self._current_story = story

    # TODO: Somehow support "startup_url" in browser_options (or remove
    # altogether), and extra_browser_args.
    self._browser = self._possible_browser.Create(self._options, started=False)
    with self._browser.StartEnvironment():
      story.LaunchBrowser(self.platform)

  def RunStory(self, _):
    self._current_story.Run(self)

  def DidRunStory(self, results):
    self._browser.Close()
    self._browser = None
    self._current_story = None

  def DumpStateUponFailure(self, story, results):
    ## TODO: Usually dumps the state of the existing browser.
    ## No implementation uses story/results, should be removed?
    pass

  def CanRunStory(self, story):
    ## TODO: Follow up, is this method really needed?
    return True


class AndroidGoFooStory(story_module.Story):
  NAME = 'foo:bar:baz'

  def __init__(self):
    super(AndroidGoFooStory, self).__init__(
        SharedAndroidStoryState, name=type(self).NAME)

  def LaunchBrowser(self, platform):
    url = 'https://en.wikipedia.org/wiki/Main_Page'
    platform._platform_backend.device.StartActivity(
        intent.Intent(package='com.google.android.apps.chrome',
                      activity='com.google.android.apps.chrome.Main',
                      action=None, data=url, category=None, extras=None),
        blocking=True)

  def Run(self, shared_state):
    current_tab = shared_state.browser.foreground_tab
    current_tab.WaitForDocumentReadyStateToBeComplete()
    action_runner = action_runner_module.ActionRunner(current_tab)
    action_runner.RepeatableBrowserDrivenScroll(repeat_count=2)



class AndroidGoStories(story_module.StorySet):
  def __init__(self):
    super(AndroidGoStories, self).__init__()
    self.AddStory(AndroidGoFooStory())


@benchmark.Owner(emails=['perezju@chromium.org'])
class AndroidGoBenchmark(benchmark.Benchmark):
  def CreateCoreTimelineBasedMeasurementOptions(self):
    cat_filter = chrome_trace_category_filter.ChromeTraceCategoryFilter(
        filter_string='rail,toplevel')
    cat_filter.AddIncludedCategory('accessibility')

    options = timeline_based_measurement.Options(cat_filter)
    options.config.enable_chrome_trace = True
    options.config.enable_cpu_trace = True
    options.SetTimelineBasedMetrics([
        'clockSyncLatencyMetric',
        'cpuTimeMetric',
        'tracingMetric',
        'accessibilityMetric',
    ])
    return options

  def CreateStorySet(self, options):
    return AndroidGoStories()

  @classmethod
  def Name(cls):
    return 'android_go.example'
