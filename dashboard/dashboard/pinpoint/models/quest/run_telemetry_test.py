# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Quest and Execution for running a Telemetry benchmark in Swarming."""

import copy
import json
import shlex

from dashboard.pinpoint.models.quest import run_test


_SWARMING_EXTRA_ARGS = (
    '--isolated-script-test-output', '${ISOLATED_OUTDIR}/output.json',
    '--isolated-script-test-chartjson-output',
    '${ISOLATED_OUTDIR}/chartjson-output.json',
)


class RunTelemetryTest(run_test.RunTest):

  def Start(self, change, isolate_hash, extra_args=()):
    # For results2 to differentiate between runs, we need to add the
    # Telemetry parameter `--results-label <change>` to the runs.
    extra_args = copy.copy(extra_args or self._extra_args)
    extra_args += ('--results-label', str(change))

    return super(RunTelemetryTest, self).Start(
        change, isolate_hash, extra_args)

  @classmethod
  def FromDict(cls, arguments):
    swarming_extra_args = []

    benchmark = arguments.get('benchmark')
    if not benchmark:
      raise TypeError('Missing "benchmark" argument.')
    swarming_extra_args.append(benchmark)

    dimensions = _GetDimensions(arguments)

    story = arguments.get('story')
    if story:
      swarming_extra_args += ('--story-filter', story)

    # TODO: Workaround for crbug.com/677843.
    if (benchmark.startswith('startup.warm') or
        benchmark.startswith('start_with_url.warm')):
      swarming_extra_args += ('--pageset-repeat', '2')
    else:
      swarming_extra_args += ('--pageset-repeat', '1')

    browser = arguments.get('browser')
    if not browser:
      raise TypeError('Missing "browser" argument.')
    swarming_extra_args += ('--browser', browser)

    extra_test_args = arguments.get('extra_test_args')
    if extra_test_args:
      # We accept a json list, or a string. If it can't be loaded as json, we
      # fall back to assuming it's a string argument.
      try:
        extra_test_args = json.loads(extra_test_args)
      except ValueError:
        extra_test_args = shlex.split(extra_test_args)
      if not isinstance(extra_test_args, list):
        raise TypeError('extra_test_args must be a list: %s' % extra_test_args)
      swarming_extra_args += extra_test_args

    swarming_extra_args += (
        '-v', '--upload-results', '--output-format', 'histograms')
    swarming_extra_args += _SWARMING_EXTRA_ARGS
    if browser == 'android-webview':
      # TODO: Share code with the perf waterfall configs. crbug.com/771680
      swarming_extra_args += ('--webview-embedder-apk',
                              '../../out/Release/apks/SystemWebViewShell.apk')

    return cls(dimensions, swarming_extra_args)


def _GetDimensions(arguments):
  dimensions = arguments.get('dimensions')
  if not dimensions:
    raise TypeError('Missing a "dimensions" argument.')

  if isinstance(dimensions, basestring):
    dimensions = json.loads(dimensions)

  return dimensions
