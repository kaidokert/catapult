# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Defines the commands provided by Telemetry: Run, List."""

from __future__ import print_function

import sys

from telemetry import benchmark
from telemetry import benchmark_list
from telemetry.internal.browser import browser_finder
from telemetry.internal.browser import browser_options
from telemetry.internal import story_runner
from telemetry.util import matching


class List(object):
  """Lists the available benchmarks"""
  @classmethod
  def AddCommandLineArgs(cls, parser, args, environment):
    del args, environment  # Unused.
    parser.add_option('--json', action='store', dest='json_filename',
                      help='Output the list in JSON')

  @classmethod
  def CreateParser(cls):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser('%prog list [benchmark_name] [<options>]')
    return parser

  @classmethod
  def ProcessCommandLineArgs(cls, parser, options, environment):
    if not options.positional_args:
      options.benchmarks = environment.GetBenchmarks()
    elif len(options.positional_args) == 1:
      options.benchmarks = _FuzzyMatchBenchmarkNames(
          options.positional_args[0], environment.GetBenchmarks())
    else:
      parser.error('Must provide at most one benchmark name.')

  def Run(self, options):
    if options.browser_type is not None:
      possible_browser = browser_finder.FindBrowser(options)
    else:
      possible_browser = None
    benchmark_list.PrintBenchmarkList(
        options.benchmarks, possible_browser,
        output_json_file=options.json_filename)
    return 0


class Run(object):
  """Run one or more benchmarks (default)"""

  @classmethod
  def CreateParser(cls):
    options = browser_options.BrowserFinderOptions()
    parser = options.CreateParser('%prog run benchmark_name [<options>]')
    return parser

  @classmethod
  def AddCommandLineArgs(cls, parser, args, environment):
    story_runner.AddCommandLineArgs(parser)

    # Allow benchmarks to add their own command line options.
    matching_benchmarks = []
    for arg in args:
      matching_benchmark = environment.GetBenchmarkByName(arg)
      if matching_benchmark is not None:
        matching_benchmarks.append(matching_benchmark)

    if matching_benchmarks:
      # TODO(dtu): After move to argparse, add command-line args for all
      # benchmarks to subparser. Using subparsers will avoid duplicate
      # arguments.
      matching_benchmark = matching_benchmarks.pop()
      matching_benchmark.AddCommandLineArgs(parser)
      # The benchmark's options override the defaults!
      matching_benchmark.SetArgumentDefaults(parser)

  @classmethod
  def ProcessCommandLineArgs(cls, parser, options, environment):
    all_benchmarks = environment.GetBenchmarks()
    if not options.positional_args:
      possible_browser = (browser_finder.FindBrowser(options)
                          if options.browser_type else None)
      benchmark_list.PrintBenchmarkList(all_benchmarks, possible_browser)
      parser.error('missing required argument: benchmark_name')

    benchmark_name = options.positional_args[0]
    benchmark_class = environment.GetBenchmarkByName(benchmark_name)
    if benchmark_class is None:
      most_likely_matched_benchmarks = matching.GetMostLikelyMatchedObject(
          all_benchmarks, benchmark_name, lambda x: x.Name())
      if most_likely_matched_benchmarks:
        print('Do you mean any of those benchmarks below?', file=sys.stderr)
        benchmark_list.PrintBenchmarkList(
            most_likely_matched_benchmarks,
            possible_browser=None, stream=sys.stderr)
      parser.error('no such benchmark: %s' % benchmark_name)

    if len(options.positional_args) > 1:
      parser.error(
          'unrecognized arguments: %s' % ' '.join(options.positional_args[1:]))

    assert issubclass(benchmark_class,
                      benchmark.Benchmark), ('Trying to run a non-Benchmark?!')

    story_runner.ProcessCommandLineArgs(parser, options, environment)
    benchmark_class.ProcessCommandLineArgs(parser, options)

    cls._benchmark = benchmark_class

  def Run(self, options):
    b = self._benchmark()
    return min(255, b.Run(options))


def _FuzzyMatchBenchmarkNames(benchmark_name, benchmark_classes):
  def _Matches(input_string, search_string):
    if search_string.startswith(input_string):
      return True
    for part in search_string.split('.'):
      if part.startswith(input_string):
        return True
    return False

  return [
      cls for cls in benchmark_classes if _Matches(benchmark_name, cls.Name())]
