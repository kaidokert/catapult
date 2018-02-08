#!/usr/bin/env python
# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys

MAIN_DIR = os.path.dirname(__file__)
TELEMETRY_DIR = os.path.realpath(os.path.join(MAIN_DIR, '..'))
TOOLS_PERF_DIR = os.path.realpath(os.path.join(
    TELEMETRY_DIR, '..', '..', '..', 'tools', 'perf'))
BENCHMARKS_DIR = os.path.realpath(os.path.join(MAIN_DIR, 'benchmarks'))

sys.path.insert(1, TELEMETRY_DIR)
sys.path.append(TOOLS_PERF_DIR)

from telemetry import benchmark_runner

from chrome_telemetry_build import chromium_config  # pylint: disable=import-error


def main():
  config = chromium_config.ChromiumConfig(
      benchmark_dirs=[BENCHMARKS_DIR],
      top_level_dir=MAIN_DIR)
  return benchmark_runner.main(config, [])


if __name__ == '__main__':
  sys.exit(main())
