# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from typ import expectations_parser
from typ import json_results

ResultType = json_results.ResultType

class StoryExpectations(object):

  def __init__(self):
    self._tags = []
    self._benchmark_name = ''
    self._typ_expectations = (
        expectations_parser.TestExpectations())
    self._raw_data = ''

  def GetBenchmarkExpectationsFromParser(self, raw_data, benchmark):
    self._raw_data = raw_data
    self._benchmark_name = benchmark
    ret, message = self._typ_expectations.parse_tagged_list(self._raw_data)
    assert not ret, 'Expectations parser error: %s' % message

  def SetTags(self, tags):
    self._typ_expectations.set_tags(tags)

  def AsDict(self):
    # TODO(rmhasan) Implement function in
    # typ.expectations_parser.TestExpectations to serialize its data
    # then transform that information into a dictionary of disabled
    # platforms for the benchmark and disabled stories with in the
    # benchmark.
    raise NotImplementedError

  def GetBrokenExpectations(self, story_set):
    # TODO(rmhasan) Implement function in
    # typ.expectations_parser.TestExpectations to get broken expectations
    del story_set
    return []

  def SetExpectations(self):
    raise NotImplementedError

  def _Freeze(self):
    raise NotImplementedError

  @property
  def disabled_platforms(self):
    raise NotImplementedError

  def DisableBenchmark(self, conditions, reason):
    raise NotImplementedError

  def IsBenchmarkDisabled(self, platform, finder_options):
    del platform, finder_options
    expected_results, _, reasons = self._typ_expectations.expectations_for(
        self._benchmark_name + '/')
    if ResultType.Skip in expected_results:
      return reasons.pop() if reasons else 'No reason given'
    return ''

  def DisableStory(self, story_name, conditions, reason):
    raise NotImplementedError

  def IsStoryDisabled(self, story, platform, finder_options):
    del platform, finder_options
    expected_results, _, reasons = self._typ_expectations.expectations_for(
        self._benchmark_name + '/' + story.name)
    if ResultType.Skip in expected_results:
      return reasons.pop() if reasons else 'No reason given'
    return ''
