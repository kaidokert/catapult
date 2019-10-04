# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import optparse
import re

from telemetry.internal.util import command_line


class _StoryMatcher(object):
  def __init__(self, pattern):
    self._regex = None
    self.has_compile_error = False
    if pattern:
      try:
        self._regex = re.compile(pattern)
      except re.error:
        self.has_compile_error = True

  def __nonzero__(self):
    return self._regex is not None

  def HasMatch(self, story):
    return self and bool(self._regex.search(story.name))


class _StoryTagMatcher(object):
  def __init__(self, tags_str):
    self._tags = tags_str.split(',') if tags_str else None

  def __nonzero__(self):
    return self._tags is not None

  def HasLabelIn(self, story):
    return self and bool(story.tags.intersection(self._tags))


class StoryFilter(command_line.ArgumentHandlerMixIn):
  """Filters stories in the story set based on command-line flags."""

  def __init__(self, benchmark_name, platform_tags):
    self._expectations = typ_expectations.StoryExpectations(benchmark_name)
    self._expectations.SetTags(platform_tags)
    if self._expectations_file and os.path.exists(self._expectations_file):
      with open(self._expectations_file) as fh:
        self._expectations.GetBenchmarkExpectationsFromParser(fh.read())

  @classmethod
  def AddCommandLineArgs(cls, parser):
    group = optparse.OptionGroup(parser, 'User story filtering options')
    group.add_option(
        '--story-filter',
        help='Use only stories whose names match the given filter regexp.')
    group.add_option(
        '--story-filter-exclude',
        help='Exclude stories whose names match the given filter regexp.')
    group.add_option(
        '--story-tag-filter',
        help='Use only stories that have any of these tags')
    group.add_option(
        '--story-tag-filter-exclude',
        help='Exclude stories that have any of these tags')
    common_story_shard_help = (
        'Indices start at 0, and have the same rules as python slices,'
        ' e.g.  [4, 5, 6, 7, 8][0:3] -> [4, 5, 6])')
    group.add_option(
        '--story-shard-begin-index', type='int', dest='story_shard_begin_index',
        help=('Beginning index of set of stories to run. If this is ommited, '
              'the starting index will be from the first story in the benchmark'
              + common_story_shard_help))
    group.add_option(
        '--story-shard-end-index', type='int', dest='story_shard_end_index',
        help=('End index of set of stories to run. Value will be '
              'rounded down to the number of stories. Negative values not'
              'allowed. If this is ommited, the end index is the final story'
              'of the benchmark. '+ common_story_shard_help))
    # This should be renamed to --also-run-disabled-stories.
    group.add_option('-d', '--also-run-disabled-tests',
                     dest='run_disabled_stories',
                     action='store_true', default=False,
                     help='Ignore expectations.config disabling.')

    parser.add_option_group(group)

  @classmethod
  def ProcessCommandLineArgs(cls, parser, args, environment):
    cls._include_regex = _StoryMatcher(args.story_filter)
    cls._exclude_regex = _StoryMatcher(args.story_filter_exclude)

    cls._include_tags = _StoryTagMatcher(args.story_tag_filter)
    cls._exclude_tags = _StoryTagMatcher(args.story_tag_filter_exclude)

    cls._begin_index = args.story_shard_begin_index or 0
    cls._end_index = args.story_shard_end_index

    if cls._end_index is not None:
      if cls._end_index < 0:
        raise parser.error(
            '--story-shard-end-index cannot be less than 0')
      if cls._begin_index is not None and cls._end_index <= cls._begin_index:
        raise parser.error(
            '--story-shard-end-index cannot be less than'
            ' or equal to --experimental-story-shard-begin-index')

    if cls._include_regex.has_compile_error:
      raise parser.error('--story-filter: Invalid regex.')
    if cls._exclude_regex.has_compile_error:
      raise parser.error('--story-filter-exclude: Invalid regex.')

    if environment.expectations_files:
      assert len(environment.expectations_files) == 1
      cls._expectations_file = environment.expectations_files[0]
    else:
      cls._expectations_file = None
    cls._run_disabled_stories = args.run_disabled_stories

  @classmethod
  def FilterStories(cls, stories):
    """Filters the given stories, using filters provided in the command line.

    This filter causes stories to become completely ignored, and therefore
    they will not show up in test results output.

    Story sharding is done before exclusion and inclusion is done.

    Args:
      stories: A list of stories.

    Returns:
      A list of remaining stories.
    """
    # TODO(crbug.com/982027): Support for --story=<exact story name>
    # should be implemented here.
    if cls._begin_index < 0:
      cls._begin_index = 0
    if cls._end_index is None:
      cls._end_index = len(stories)

    stories = stories[cls._begin_index:cls._end_index]

    final_stories = []
    for story in stories:
      # Exclude filters take priority.
      if cls._exclude_tags.HasLabelIn(story):
        continue
      if cls._exclude_regex.HasMatch(story):
        continue

      if cls._include_tags and not cls._include_tags.HasLabelIn(story):
        continue
      if cls._include_regex and not cls._include_regex.HasMatch(story):
        continue

      final_stories.append(story)

    return final_stories

  def ShouldSkip(self, story):
    """Decides whether a story should be marked skipped.

    The difference between marking a story skipped and simply not running
    it is important for tracking purposes. Officially skipped stories show
    up in test results outputs.

    Args:
      story: A story.Story object.

    Returns:
      True if the story should be skipped and False otherwise.
    """
    # TODO(crbug.com/982027): Support for --story=<exact story name>
    # should be implemented here.
    disabled = self._expectations.IsStoryDisabled(story)
    if disabled and self._run_disabled_stories:
      logging.warning('Force running a disabled story: %s' %
                      story.name)
      return False
    return disabled
