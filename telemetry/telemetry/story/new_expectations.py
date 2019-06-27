# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from collections import defaultdict
from typ import expectations_parser
from typ import json_results

ResultType = json_results.ResultType

class StoryExpectations(object):

  def __init__(self, tags):
    self._benchmark_disabled = False
    self._tags = tags
    self._benchmark_name = ''
    self._expectations = []
    self._typ_expectations = None
    self._dict = {}

  def GetBenchmarkExpectationsFromParser(self, expectations, benchmark):
    self._typ_expectations = expectations_parser.TestExpectations(self._tags)
    self._typ_expectations.classify_test_expectations(expectations)
    self._benchmark_name = benchmark
    self._expectations = expectations

  def AsDict(self):
    if not self._dict:
      self._dict = {'platforms': [], 'stories': defaultdict(list)}
      for exp in self._expectations:
        reason = exp.reason or 'No reason given'
        if exp.test == self._benchmark_name + '*':
          self._dict['platforms'].append((list(exp.tags), reason))
        elif (exp.test.startswith(self._benchmark_name + '/') and
              exp.test[-1] != '*'):
          self._dict['stories'][exp.test[len(self._benchmark_name)+1:]].append(
              (list(exp.tags), reason))
    return self._dict

  def GetBrokenExpectations(self, story_set):
    #TODO(rmhasan): Move this to Typ because other people need it.
    story_set_story_names = [s.name
                             for s in story_set.stories]
    invalid_expectations = []
    trie = {}
    for test in story_set_story_names:
      _trie = trie.setdefault(test[0], {})
      for l in test[1:]:
        _trie = _trie.setdefault(l, {})
      _trie.setdefault('$', {})

    for exp in self._expectations:
      if (not exp.test.startswith(self._benchmark_name + '/') or
          exp.test[-1] == '*'):
        continue
      _trie = trie
      is_glob = False
      already_invalid = False
      pattern = exp.test[len(self._benchmark_name)+1:]

      for l in pattern:
        if l == '*':
          is_glob = True
          break
        if not l in _trie:
          invalid_expectations.append(pattern)
          already_invalid = True
          break
        _trie = _trie[l]
      if not already_invalid and not is_glob and '$' not in _trie:
        invalid_expectations.append(pattern)

    for story_name in invalid_expectations:
      logging.error('Story %s is not in the story set.' % story_name)
    return invalid_expectations

  # TODO(rnephew): When TA/DA conversion is complete, remove this method.
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
    #TODO(rmhasan): Need to get reason for disabling
    del platform, finder_options
    expected_results, _ = self._typ_expectations.expectations_for(
        self._benchmark_name)
    return ResultType.Skip in expected_results

  def DisableStory(self, story_name, conditions, reason):
    raise NotImplementedError

  def IsStoryDisabled(self, story, platform, finder_options):
    del platform, finder_options
    expected_results, _ = self._typ_expectations.expectations_for(
        self._benchmark_name + '/' + story.name)
    return ResultType.Skip in expected_results
