# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function

import json
import logging
import optparse

from telemetry import benchmark


def PrintBenchmarkList(benchmarks, possible_browser=None, stream=None,
                       output_json_file=None):
  """Extract and list information about the given benchmarks.

  Args:
    benchmarks: A list of benchmark classes for which to list info.
    possible_browser: An optional possible_browser instance used for checking
      which benchmarks are supported on that browser.
    stream: An optional file-like stream where to write the list output,
      defaults to stdout.
    output_json_file: An optional string with a file path. If given, the
      benchmark info is also serialized to that file in a machine readable form.
  """
  all_benchmark_info = [
      GetBenchmarkInfo(b, possible_browser)  for b in benchmarks]
  all_benchmark_info.sort(key=lambda b: b['name'])

  if output_json_file is not None:
    with open(output_json_file, 'w') as f:
      json.dump(all_benchmark_info, f, sort_keys=True, indent=4,
                separators=(',', ': '))

  # Align the benchmark names to the longest one.
  format_string = '  %%-%ds %%s' % max(len(b['name'])
                                       for b in all_benchmark_info)

  grouped = {'supported': [], 'not_supported': []}
  for b in all_benchmark_info:
    label = 'supported' if b.get('supported', True) else 'not_supported'
    grouped[label].append(b)
  if grouped['supported']:
    print('Available benchmarks', end=' ', file=stream)
    if possible_browser:
      print('for', possible_browser.browser_type, end=' ', file=stream)
    print('are:', file=stream)
    for b in grouped['supported']:
      print(format_string % (b['name'], b['description']), file=stream)
    print(file=stream)
  if grouped['not_supported']:
    print('Not supported benchmarks for', possible_browser.browser_type,
          'are (force run with -d):', file=stream)
    for b in grouped['not_supported']:
      print(format_string % (b['name'], b['description']), file=stream)
    print(file=stream)

  print('Pass --browser to list benchmarks for',
        'another' if possible_browser is not None else 'a specific',
        'browser.', file=stream)


def GetBenchmarkInfo(benchmark_class, possible_browser=None):
  """Get a json serializable dict with information about a given benchmark.

  Args:
    benchmark_class: A benchmark.Benchmark subclass from which to extract info.
    possible_browser: An optional possible_browser instance used for checking
      whether the benchmark is supported on that browser.

  Returns:
    A json serializable dict with the following contents:

      {
          "name": <string>,
          "description": <string>,
          "supported": <boolean>,
          "enabled": <boolean>,
          "stories": [
              {
                  "name": <string>,
                  "description": <string>,
                  "tags": [<string>, ...]
              }
              ...
          ]
      }

    Note that "supported" simply checks whether the browser's platform is
    listed in the benchmark's SUPPORTED_PLATFORMS. The "enabled" field is
    deprecated and carries the same value as "supported"; this function does
    not check, e.g., whether stories of a benchmark are disabled within the
    expectations.config file.
  """
  if not issubclass(benchmark_class, benchmark.Benchmark):
    raise TypeError('Not a benchmark class: %s' % benchmark_class)
  benchmark_obj = benchmark_class()
  info = {
      'name': benchmark_class.Name(),
      'description': benchmark_class.Description(),
      'stories': [
          {
              'name': story.name,
              'description': _DescribeStory(story),
              'tags': list(story.tags)
          }
          for story in _GetBenchmarkStories(benchmark_obj)
      ]
  }
  info['stories'].sort(key=lambda s: s['name'])
  if possible_browser is not None:
    info['supported'] = benchmark_obj.CanRunOnPlatform(
        possible_browser.platform, possible_browser)
    info['enabled'] = info['supported']  # Deprecated.
  return info


def _DescribeStory(story):
  """Get the docstring title out of a given story."""
  description = story.__doc__
  if description:
    return description.strip().splitlines()[0]
  else:
    return ''


def _GetBenchmarkStories(benchmark_obj):
  """Get all stories for a given benchmark object."""
  # Create a options object which hold default values that are expected
  # by Benchmark.CreateStoriesWithTags(options) method.
  parser = optparse.OptionParser()
  type(benchmark_obj).AddBenchmarkCommandLineArgs(parser)
  options, _ = parser.parse_args([])

  try:
    return benchmark_obj.CreateStorySet(options)
  except Exception as exc:  # pylint: disable=broad-except
    # Some benchmarks require special options, such as *.cluster_telemetry.
    # Just ignore them for now.
    logging.info(
        'Unable to get stories for %s due to "%s"', benchmark_obj.Name(), exc)
    return []
