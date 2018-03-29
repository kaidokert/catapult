# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Quest and Execution for running a GTest in Swarming."""

import json

from dashboard.pinpoint.models.quest import run_test


_SWARMING_EXTRA_ARGS = (
    '--isolated-script-test-output', '${ISOLATED_OUTDIR}/output.json',
    '--isolated-script-test-chartjson-output',
    '${ISOLATED_OUTDIR}/chartjson-output.json',
)


class RunGTest(run_test.RunTest):

  @classmethod
  def FromDict(cls, arguments):
    swarming_extra_args = []

    dimensions = _GetDimensions(arguments)

    test = arguments.get('test')
    if test:
      swarming_extra_args.append('--gtest_filter=' + test)

    swarming_extra_args.append('--gtest_repeat=1')

    extra_test_args = arguments.get('extra_test_args')
    if extra_test_args:
      extra_test_args = json.loads(extra_test_args)
      if not isinstance(extra_test_args, list):
        raise TypeError('extra_test_args must be a list: %s' % extra_test_args)
      swarming_extra_args += extra_test_args

    swarming_extra_args += _SWARMING_EXTRA_ARGS

    return cls(dimensions, swarming_extra_args)


def _GetDimensions(arguments):
  dimensions = arguments.get('dimensions')
  if not dimensions:
    raise TypeError('Missing a "dimensions" argument.')

  if isinstance(dimensions, basestring):
    dimensions = json.loads(dimensions)

  return dimensions
