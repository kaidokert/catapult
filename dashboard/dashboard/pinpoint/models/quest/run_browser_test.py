# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Quest for running a browser test in Swarming."""

from dashboard.pinpoint.models.quest import run_test


_DEFAULT_EXTRA_ARGS = ['--test-launcher-bot-mode']


class RunBrowserTest(run_test.RunTest):

  @classmethod
  def _ExtraTestArgs(cls, arguments):
    extra_test_args = []

    # The browser test launcher only properly parses arguments in the
    # --key=value format.
    test_filter = arguments.get('test-filter')
    if test_filter:
      extra_test_args.append('--gtest_filter=%s' % test_filter)

    num_retries = arguments.get('num-retries')
    if num_retries:
      num_retries = int(num_retries)
      if num_retries < 0:
        raise TypeError('Given a negative retry number.')
      extra_test_args.append('--test-launcher-retry-limit=%d' % num_retries)

    num_repeats = arguments.get('num-repeats')
    if num_repeats:
      num_repeats = int(num_repeats)
      if num_repeats < 0:
        raise TypeError(
            'Given a negative repeat number, which would run test endlessly.')
      extra_test_args.append('--gtest_repeat=%d' % num_repeats)

    extra_test_args += _DEFAULT_EXTRA_ARGS
    extra_test_args += super(RunBrowserTest, cls)._ExtraTestArgs(arguments)
    return extra_test_args
