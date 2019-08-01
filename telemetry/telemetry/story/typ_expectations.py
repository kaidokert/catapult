# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''This module implements the StoryExpectations class which is a wrapper
around typ's expectations_parser module.

Example:
  expectations = typ_expectations.StoryExpectations(benchmark1)
  expectations.GetBenchmarkExpectationsFromParser(file_content)
  disabled_benchmark = expectations.IsBenchmarkDisabled(None, None)
  disabled_story = expectations.IsStoryDisabled('story1', None, None)
'''

from typ import expectations_parser
from typ import json_results


ResultType = json_results.ResultType


class StoryExpectations(object):

  def __init__(self, benchmark_name):
    self._benchmark_name = benchmark_name
    self._typ_expectations = (
        expectations_parser.TestExpectations())

  def GetBenchmarkExpectationsFromParser(self, raw_data):
    error, message = self._typ_expectations.parse_tagged_list(raw_data)
    assert not error, 'Expectations parser error: %s' % message

  def SetTags(self, tags):
    self._typ_expectations.set_tags(tags)

  def serialize(self):
    def _serialize_expectation(exp):
      return {'reason':  (exp.reason or ''),
              'conditions': sorted(exp.tags),
              'line_number': exp.lineno}
    patterns_to_exps = {
        k:v for k, v in self._typ_expectations.individual_exps.items()
        if k.startswith(self._benchmark_name + '/')}
    patterns_to_exps.update(
        {k:v for k, v in self._typ_expectations.glob_exps.items()
         if k.startswith(self._benchmark_name + '/')})
    return {'tags': sorted(self._typ_expectations.tags),
            'expectations': {
                pattern: [_serialize_expectation(exp) for exp in expectations]
                for pattern, expectations in patterns_to_exps.items()}}

  def GetBrokenExpectations(self, story_set):
    # TODO(crbug.com/973936):  Implement function in
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

  def DisableStory(self, story_name, conditions, reason):
    raise NotImplementedError

  def _IsStoryOrBenchmarkDisabled(self, pattern):
    expected_results, _, reasons = self._typ_expectations.expectations_for(
        pattern)
    if ResultType.Skip in expected_results:
      return reasons.pop() if reasons else 'No reason given'
    return ''

  def IsBenchmarkDisabled(self, platform, finder_options):
    # TODO(crbug.com/973936): Remove platform and finder_options arguments
    # after removing the expectations module.
    del platform, finder_options
    return self._IsStoryOrBenchmarkDisabled(self._benchmark_name + '/')

  def IsStoryDisabled(self, story, platform, finder_options):
    # TODO(crbug.com/973936): Remove platform and finder_options arguments
    # after removing the expectations module.
    del platform, finder_options
    return self._IsStoryOrBenchmarkDisabled(
        self._benchmark_name + '/' + story.name)
