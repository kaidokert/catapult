# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Quest for running a Telemetry benchmark in Swarming."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import copy
import re

from dashboard.pinpoint.models.quest import run_performance_test


_DEFAULT_EXTRA_ARGS = [
    '-v', '--upload-results', '--output-format', 'histograms']

_STORY_REGEX = re.compile(r'[^a-zA-Z0-9]')


def _StoryToRegex(story_name):
  # Telemetry's --story-filter argument takes in a regex, not a
  # plain string. Stories can have all sorts of special characters
  # in their names (see crbug.com/983993) which would confuse a
  # regex. We thus keep only a small set of "safe chars"
  # and replace all others with match-any-character regex dots.
  return '^%s$' % _STORY_REGEX.sub('.', story_name)


class RunTelemetryTest(run_performance_test.RunPerformanceTest):

  def Start(self, change, isolate_server, isolate_hash):
    # For results2 to differentiate between runs, we need to add the
    # Telemetry parameter `--results-label <change>` to the runs.
    extra_args = copy.copy(self._extra_args)
    extra_args += ('--results-label', str(change))
    extra_swarming_tags = {'change': str(change)}

    return self._Start(change, isolate_server, isolate_hash, extra_args,
                       extra_swarming_tags)

  @classmethod
  def _ExtraTestArgs(cls, arguments):
    extra_test_args = []

    benchmark = arguments.get('benchmark')
    if not benchmark:
      raise TypeError('Missing "benchmark" argument.')
    extra_test_args += ('--benchmarks', benchmark)

    story = arguments.get('story')
    if story:
      # TODO(crbug.com/982027): Note that the following two arguments
      # may be replaced with --story=<story> (no regex needed). Support
      # for --story flag landed in
      # https://chromium-review.googlesource.com/c/catapult/+/1869800
      # so we cannot turn this on by default until we no longer need to
      # be able to run revisions older than that. In the meantime, the
      # following arguments accomplish the same thing.
      extra_test_args += ('--story-filter', _StoryToRegex(story))
      # Since benchmarks are run in abridged form by default, we need to
      # add the argument --run-full-story-set to make sure that if someone
      # chooses to run a specific story we will run it even if it is not
      # in the abridged version of the story set.
      extra_test_args.append('--run-full-story-set')

    story_tags = arguments.get('story_tags')
    if story_tags:
      extra_test_args += ('--story-tag-filter', story_tags)

    # TODO: Workaround for crbug.com/677843.
    if (benchmark.startswith('startup.warm') or
        benchmark.startswith('start_with_url.warm')):
      extra_test_args += ('--pageset-repeat', '2')
    else:
      extra_test_args += ('--pageset-repeat', '1')

    browser = arguments.get('browser')
    if not browser:
      raise TypeError('Missing "browser" argument.')
    extra_test_args += ('--browser', browser)

    if browser.startswith('android-webview'):
      # TODO: Share code with the perf waterfall configs. crbug.com/771680
      extra_test_args += ('--webview-embedder-apk',
                          '../../out/Release/apks/SystemWebViewShell.apk')

    extra_test_args += _DEFAULT_EXTRA_ARGS
    extra_test_args += super(RunTelemetryTest, cls)._ExtraTestArgs(arguments)
    return extra_test_args

  @classmethod
  def _GetSwarmingTags(cls, arguments):
    tags = {}
    benchmark = arguments.get('benchmark')
    if not benchmark:
      raise TypeError('Missing "benchmark" argument.')
    tags['benchmark'] = benchmark
    story_filter = arguments.get('story')
    tag_filter = arguments.get('story_tags')
    tags['hasfilter'] = '1' if story_filter or tag_filter else '0'
    if story_filter:
      tags['storyfilter'] = story_filter
    if tag_filter:
      tags['tagfilter'] = tag_filter
    return tags
