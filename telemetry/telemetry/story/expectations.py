# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os


class ParseError(Exception):
  pass


class TestExpectationParser(object):
  """Parse expectations file.

  This parser covers the 'tagged' test lists format in:
      go/chromium-test-list-format.

  It takes the path to the expectation file as an argument.

  Example expectation file to parse:
    # This is an example expectation file.
    #
    # tags: Mac Mac10.10 Mac10.11
    # tags: Win Win8

    crbug.com/123 [ Win ] benchmark/story [ Skip ]
  """
  def __init__(self, path):
    assert os.path.exists(path), 'Path to expectation file must exist.'
    self._path = path
    self._tags = []
    self._expectations = []
    self._ParseExpectationFile(path)

  def _ParseExpectationFile(self, path):
    with open(path, 'r') as fp:
      raw_data = fp.read()
    for line in raw_data.splitlines():
      # Handle metadata and comments.
      if line.startswith('# tags:'):
        for word in line[8:].split():
          self._tags.append(word)
      elif line.startswith('#') or not line:
        continue  # Ignore, it is just a comment or empty.
      else:
        self._expectations.append(self._ParseExpectationLine(line, self._tags))

  @staticmethod
  def _ParseExpectationLine(line, tags):
    e = {
        'reason': None,
        'conditions': [],
        'results': []
    }
    # These keep track of where in the parsing process we are.
    in_conditions = False
    finished_conditions = False
    in_results = False
    finished_results = False
    for word in line.split():
      # Detect error states.
      if word == ']' and not in_conditions and not in_results:
        raise ParseError('Found ] when not in condition or result section.')
      if word == '[' and (in_conditions or in_results):
        raise ParseError('Found [ when already in condition or results.')
      # Detect bug information.
      elif word.startswith('crbug') or word.startswith('Bug('):
        assert not e.get('reason'), 'Bug already detected'
        e['reason'] = word
      # Detect test name
      elif not in_conditions and word != '[' and not e.get('test'):
        # Test name is after condition. If name is set we are past conditions.
        finished_conditions = True
        e['test'] = word
      # Detect start of platform/results listing.
      elif word == '[':
        if not finished_conditions:
          in_conditions = True
        else:
          in_results = True

      # Special conditions/results modes after this.
      elif in_conditions:
        # Detect end of condtions listing.
        if word == ']':
          in_conditions = False
          finished_conditions = True
        else:
          e['conditions'].append(word)
      elif in_results:
        # Detect end of results.
        if word == ']':
          in_results = False
          finished_results = True
        else:
          e['results'].append(word)
      # If this triggers, we are in an unanticipated state.
      else:
        raise ParseError('Parser in unknown state mid expectation.\n '
                         'Line:%s \n Token:%s' % (line, word))
    if not (e['test'] and finished_conditions and finished_results):
      raise ParseError('Parsing did not end in a valid final state.\n %s' % e)
    for tag in e['conditions']:
      assert tag in tags
    return e

  @property
  def expectations(self):
    return self._expectations

  @property
  def tags(self):
    return self._tags


class StoryExpectations(object):
  """An object that contains disabling expectations for benchmarks and stories.

  Example Usage:
  class FooBenchmarkExpectations(expectations.StoryExpectations):
    def SetExpectations(self):
      self.DisableBenchmark(
          [expectations.ALL_MOBILE], 'Desktop Benchmark')
      self.DisableStory('story_name1', [expectations.ALL_MAC], 'crbug.com/456')
      self.DisableStory('story_name2', [expectations.ALL], 'crbug.com/789')
      ...
  """
  def __init__(self, expectation_file=None):
    self._disabled_platforms = []
    self._expectations = {}
    self._frozen = False
    self.SetExpectations()
    if expectation_file:
      parser = TestExpectationParser(expectation_file)
      self._MapExpectationsFromFile(parser)
    self._Freeze()

  # TODO(rnephew): Transform parsed expectation file into StoryExpectations.
  # crbug.com/781409
  def _MapExpectationsFromFile(self, _):
    pass

  def AsDict(self):
    """Returns information on disabled stories/benchmarks as a dictionary"""
    return {
        'platforms': self._disabled_platforms,
        'stories': self._expectations
    }

  def GetBrokenExpectations(self, story_set):
    story_set_story_names = [s.name for s in story_set.stories]
    invalid_story_names = []
    for story_name in self._expectations:
      if story_name not in story_set_story_names:
        invalid_story_names.append(story_name)
        logging.error('Story %s is not in the story set.' % story_name)
    return invalid_story_names

  def SetExpectations(self):
    """Sets the Expectations for test disabling

    Override in subclasses to disable tests."""
    pass

  def _Freeze(self):
    self._frozen = True
    self._disabled_platforms = tuple(self._disabled_platforms)

  @property
  def disabled_platforms(self):
    return self._disabled_platforms

  def DisableBenchmark(self, conditions, reason):
    """Temporarily disable failing benchmarks under the given conditions.

    This means that even if --also-run-disabled-tests is passed, the benchmark
    will not run. Some benchmarks (such as system_health.mobile_* benchmarks)
    contain android specific commands and as such, cannot run on desktop
    platforms under any condition.

    Example:
      DisableBenchmark(
          [expectations.ALL_MOBILE], 'Desktop benchmark')

    Args:
      conditions: List of _TestCondition subclasses.
      reason: Reason for disabling the benchmark.
    """
    assert reason, 'A reason for disabling must be given.'
    assert not self._frozen, ('Cannot disable benchmark on a frozen '
                              'StoryExpectation object.')
    for condition in conditions:
      assert isinstance(condition, _TestCondition)

    self._disabled_platforms.append((conditions, reason))

  def IsBenchmarkDisabled(self, platform, finder_options):
    """Returns the reason the benchmark was disabled, or None if not disabled.

    Args:
      platform: A platform object.
    """
    for conditions, reason in self._disabled_platforms:
      for condition in conditions:
        if condition.ShouldDisable(platform, finder_options):
          logging.info('Benchmark permanently disabled on %s due to %s.',
                       condition, reason)
          return reason
    return None

  def DisableStory(self, story_name, conditions, reason):
    """Disable the story under the given conditions.

    Example:
      DisableStory('story_name', [expectations.ALL_WIN], 'crbug.com/123')

    Args:
      story_name: Name of the story to disable passed as a string.
      conditions: List of _TestCondition subclasses.
      reason: Reason for disabling the story.
    """
    assert reason, 'A reason for disabling must be given.'
    # TODO(rnephew): Remove http check when old stories that use urls as names
    # are removed.
    if not story_name.startswith('http'):
      # Decrease to 50 after we shorten names of existing tests.
      assert len(story_name) < 75, (
          "Story name exceeds limit of 75 characters. This limit is in place to"
          " encourage Telemetry benchmark owners to use short, simple story "
          "names (e.g. 'google_search_images', not "
          "'http://www.google.com/images/1234/abc')."

      )
    assert not self._frozen, ('Cannot disable stories on a frozen '
                              'StoryExpectation object.')
    for condition in conditions:
      assert isinstance(condition, _TestCondition)
    if not self._expectations.get(story_name):
      self._expectations[story_name] = []
    self._expectations[story_name].append((conditions, reason))

  def IsStoryDisabled(self, story, platform, finder_options):
    """Returns the reason the story was disabled, or None if not disabled.

    Args:
      story: Story object that contains a name property.
      platform: A platform object.

    Returns:
      Reason if disabled, None otherwise.
    """
    for conditions, reason in self._expectations.get(story.name, []):
      for condition in conditions:
        if condition.ShouldDisable(platform, finder_options):
          logging.info('%s is disabled on %s due to %s.',
                       story.name, condition, reason)
          return reason
    return None


# TODO(rnephew): Since TestConditions are being used for more than
# just story expectations now, this should be decoupled and refactored
# to be clearer.
class _TestCondition(object):
  def ShouldDisable(self, platform, finder_options):
    raise NotImplementedError

  def __str__(self):
    raise NotImplementedError


class _TestConditionByPlatformList(_TestCondition):
  def __init__(self, platforms, name):
    self._platforms = platforms
    self._name = name

  def ShouldDisable(self, platform, finder_options):
    del finder_options  # Unused.
    return platform.GetOSName() in self._platforms

  def __str__(self):
    return self._name


class _AllTestCondition(_TestCondition):
  def ShouldDisable(self, platform, finder_options):
    del platform, finder_options  # Unused.
    return True

  def __str__(self):
    return 'All Platforms'


class _TestConditionAndroidSvelte(_TestCondition):
  """Matches android devices with a svelte (low-memory) build."""
  def ShouldDisable(self, platform, finder_options):
    del finder_options  # Unused.
    return platform.GetOSName() == 'android' and platform.IsSvelte()

  def __str__(self):
    return 'Android Svelte'


class _TestConditionByAndroidModel(_TestCondition):
  def __init__(self, model, name=None):
    self._model = model
    self._name = name if name else model

  def ShouldDisable(self, platform, finder_options):
    return (platform.GetOSName() == 'android' and
            self._model in platform.GetDeviceTypeName())

  def __str__(self):
    return self._name

class _TestConditionAndroidWebview(_TestCondition):
  def ShouldDisable(self, platform, finder_options):
    return (platform.GetOSName() == 'android' and
            finder_options.browser_type == 'android-webview')

  def __str__(self):
    return 'Android Webview'

class _TestConditionAndroidNotWebview(_TestCondition):
  def ShouldDisable(self, platform, finder_options):
    return (platform.GetOSName() == 'android' and not
            finder_options.browser_type == 'android-webview')

  def __str__(self):
    return 'Android but not webview'

class _TestConditionByMacVersion(_TestCondition):
  def __init__(self, version, name=None):
    self._version = version
    self._name = name

  def __str__(self):
    return self._name

  def ShouldDisable(self, platform, finder_options):
    if platform.GetOSName() != 'mac':
      return False
    return platform.GetOSVersionDetailString().startswith(self._version)


class _TestConditionLogicalAndConditions(_TestCondition):
  def __init__(self, conditions, name):
    self._conditions = conditions
    self._name = name

  def __str__(self):
    return self._name

  def ShouldDisable(self, platform, finder_options):
    return all(
        c.ShouldDisable(platform, finder_options) for c in self._conditions)


ALL = _AllTestCondition()
ALL_MAC = _TestConditionByPlatformList(['mac'], 'Mac Platforms')
ALL_WIN = _TestConditionByPlatformList(['win'], 'Win Platforms')
ALL_LINUX = _TestConditionByPlatformList(['linux'], 'Linux Platforms')
ALL_CHROMEOS = _TestConditionByPlatformList(['chromeos'], 'ChromeOS Platforms')
ALL_ANDROID = _TestConditionByPlatformList(['android'], 'Android Platforms')
ALL_DESKTOP = _TestConditionByPlatformList(
    ['mac', 'linux', 'win', 'chromeos'], 'Desktop Platforms')
ALL_MOBILE = _TestConditionByPlatformList(['android'], 'Mobile Platforms')
ANDROID_NEXUS5 = _TestConditionByAndroidModel('Nexus 5')
ANDROID_NEXUS5X = _TestConditionByAndroidModel('Nexus 5X')
ANDROID_NEXUS6 = _TestConditionByAndroidModel('Nexus 6')
ANDROID_NEXUS6P = _TestConditionByAndroidModel('Nexus 6P')
ANDROID_NEXUS7 = _TestConditionByAndroidModel('Nexus 7')
ANDROID_ONE = _TestConditionByAndroidModel(
    'W6210', 'Cherry Mobile Android One')
ANDROID_SVELTE = _TestConditionAndroidSvelte()
ANDROID_WEBVIEW = _TestConditionAndroidWebview()
ANDROID_NOT_WEBVIEW = _TestConditionAndroidNotWebview()
# MAC_10_11 Includes:
#   Mac 10.11 Perf, Mac Retina Perf, Mac Pro 10.11 Perf, Mac Air 10.11 Perf
MAC_10_11 = _TestConditionByMacVersion('10.11', 'Mac 10.11')
# Mac 10_12 Includes:
#   Mac 10.12 Perf, Mac Mini 8GB 10.12 Perf
MAC_10_12 = _TestConditionByMacVersion('10.12', 'Mac 10.12')

ANDROID_NEXUS6_WEBVIEW = _TestConditionLogicalAndConditions(
    [ANDROID_NEXUS6, ANDROID_WEBVIEW], 'Nexus6 Webview')
ANDROID_NEXUS5X_WEBVIEW = _TestConditionLogicalAndConditions(
    [ANDROID_NEXUS5X, ANDROID_WEBVIEW], 'Nexus5X Webview')
