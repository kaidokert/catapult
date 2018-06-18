# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Translate between test paths and Descriptors.

Test paths describe a timeseries by its path in a tree of timeseries.
Descriptors describe a timeseries semantically by its characteristics.
Descriptors allow users to navigate timeseries use meaningful words like
"measurement" and "test case" instead of meaningless words like "subtest".
Test paths can be arbitrarily long, but there are a fixed number of semantic
characteristics. Multiple test path components may be joined into a single
characteristic.

This translation layer should be temporary until the descriptor concept can be
pushed down into the Model layer.
"""

import hashlib


TEST_BUILD_TYPE = 'test'
REFERENCE_BUILD_TYPE = 'ref'
STATISTICS = ['avg', 'count', 'max', 'min', 'std', 'sum']


# Store hashes to prevent leaking internal-only names.

# These are test path components that must be joined with the following test
# path components in order to form a composite test suite.
PARTIAL_TEST_SUITE_HASHES = [
    hashlib.sha256('TEST_PARTIAL_TEST_SUITE').hexdigest(),
    '147e82faca64a021f4af180c2acbeaa8be6a43478105110702869e353cda8c46',
]

# These are test suites composed of 2 or more test path components.
# All composite test suites start with a partial test suite, but not all test
# suites that start with a partial test suite are composite.
COMPOSITE_TEST_SUITE_HASHES = [
    hashlib.sha256('TEST_PARTIAL_TEST_SUITE:COMPOSITE').hexdigest(),
    '6f3defc338a36507ed61085b6b29e9ac0cd8a95066f557ac6a664deafc9fc503',
    '84bcb2064732acc3a77dc629e27851e535a6b13e2f808d96c2437bed0319eb4a',
    'e9cfb0c1c412e5e049819a87c78d32d9aa12ce0e0c4a47277c7e6cd1ee22129f',
    '127edf76c9bfd5f39ce2112c67d09abed4f704360b182bb923f2af14811c8d47',
    '89d460df708abdf78bbc722c755324614c179c8d5c523120ae9e3882d4f4a920',
    '8cac414e9a2b4f0bd4cb8e065cab051ede705f3be766d47d15d66db47baec752',
    'db60c2e6510f122cc91c601f7234cb82e87a40ddcc59c7df46ff98eccf37122a',
    'a3eb4c22d502c1b1bae7afb42a31aa69b37a461002bef65e61f561dbae54f353',
    '33a41e925be99297177ae7718318f7c15f73817bf33ef40c5274e0a68c4fad50',
    'cb948a7c86446f5a6c120ca77dfea5024f942c555a0139d725dbfb29c0db7d74',
    '210a6ef892487b9a0ab882f6c724034a3bcdca1bbed6d8a3c4a48fc97214da9b',
    '93379b402f117fe6a4fafb0673dcb6e91a7396067783fc4eedc155ddc4674c9e',
    '40f23ec66c9dc358009863f354efb410cb908b6e35b26a05ec7cccbfbf334aac',
    '6a501dd89d11aaf5f18723c72142d4fbce8c896cd2651235c998afb0797553cd',
    '48ac6b6d687f87d6b5389063d9ae90662923a185d46705de6927d31479a233b3',
    'a7a07b6d79e949a8620ce809e93282ed0eb355f1b7b0b02578dc79ca92030570',
    'd4e90ebada38a5029c0e9c5cae3e3387eca45499d1cef1e6ca50124890a1d8b8',
    '8d2d2b5a0d9ceda5e978208bcaf90d497a8e91cc6685c8a25133725c563baf61',
    '692b99ee360b23545e5d3b76e0b776c818267654382a34d8c6df890e34f42379',
    '2bf796fb531e5cbff8bf04a196d3758a6b65d1b504f11e3366a6902fe91b1a86',
    'd6d362eecb896c695d945f73036e774d175aed5a5cf758f5d97266182b8a0992',
    '5a78eeca904473182733cd1073452c5d5c941130fc2728ffcdfe25235237c640',
    'dd25baf23ce594667668b838eb4321b3fce07c9bad7aef14463297bf6f63c843',
    '47605e96e58bc85a863d27ad780072cf229738e338a3f6eb595c2fdb017e99d3',
    'ffdc1402c5981f48459a2fc9563288201efcbbec0c81669f66f2cea04a651f74',
    '4bc27a2b0e1d2581aa7f07a8fe36123e8f4b4fa7674fc44766ca7a7e641afb3a',
    '61f3e26a2ad79237b5f23d211387a409df055802ff9a7f74ec1c4afd3d0be50e',
    'd4686b075579056ac99f3adfae557088241534d2db6a17964ea377d5ec43daa3',
    '8fc522eac949ebf21d09e96bd0e0ab27e948ab60718b78d9aa3df4829a90a0e0',
    '5fe7428907bfe8b86f67b6d378e6828eb81090b046902ffd42562cf7dc88f54c',
    '82634db8506881f5193bb0c965beec493b0832adb6a9b895429ea8dccc85b20c',
    '586217b9dfd0fe0f9c4bf673ec006c05f2a68fe7781c6a9da630ef54c82329ea',
    'd1bea12862dfe226e796f190a85120c24654d727d9659c750879fc2460d8bb69',
    'bbf85d2697c43c0a2e658c12bc351d5faf9474a2651abb4432cfe8f984c123f4',
    '68f6d39adec5d35ee4eb3baca16d17865e9326ab9424b7adc86fb9b562af4a9e',
    '2a1dd20563dfda50b7377f806f06de46c5ffad8d618a615cd859b3bd3b80a821',
    'bca774141490a3077d34bbbf01af4957ec1e8cad8fa37eebc4a9f62ea971ff2e',
    '0c8c88f83e3fe71314fa699cd99be2a1867a2a7e46132755c148f849152da3c5',
    'b7e4d9f4fd36f427b7eaaa0588d9aed6ffd33c9da40fd359ae21ca99cce6e58e',
    '2abd965714ff385d3ffde085ed74a1d2074198d0a468295176188a0566abedb9',
    '2603596a5a6e6a07969ab9b5e0b8f297893c5ed322fe1d26bbcbd4be3c9d7769',
    '73ab1766ae2339d37413a7f376ca5af480cfe428bd37a4ff80b25f775666f91a',
    '015c916a8957b79867652ff40b47015af35f7c1f8b22b4c2da98e1c476840c4b',
    '3d900620712d5cc18c3f943cb5ad7d9fe95de332bc10964c872e35e45d24a2bc',
    '8528beaeb1948cb89c497d37702688d01db195324f5baa5349a6e0d29e93911d',
    'd8ec9531739ba4eefe209a2dbc3f0b5be954da2cdd2d60ea09660687890ef679',
    '8ee673a89aacc827bfb6e3e551da8cdbb3bae013a4d031df56c633cb0dd48212',
    '88a953f5872982d3d782e71f06bb8e8e76f75e8bac26768f2e785ee57899a940',
    '02637d70632c7b249b50f9e849094f53407d56e5c6300d2445d0b398d12f80b0',
    '2c74dc4e60629fc0bcc621c72d376beb02c1df3bb251fec7c07d232736e83b1a',
]

GROUPABLE_TEST_SUITE_PREFIXES = [
    'TEST_GROUPABLE%',
    'autoupdate_EndToEndTest.',
    'blink_perf.',
    'cheets_',
    'graphics_',
    'smoothness.',
    'thread_times.',
    'v8.',
    'video_',
]


class Descriptor(object):
  """Describe a timeseries by its characteristics.

  Supports partial test paths (e.g. test suite paths) by allowing some
  characteristics to be None.
  """

  def __init__(self, test_suite=None, measurement=None, bot=None,
               test_case=None, statistic=None, build_type=None):
    self.test_suite = test_suite
    self.measurement = measurement
    self.bot = bot
    self.test_case = test_case
    self.statistic = statistic
    self.build_type = build_type

  def __repr__(self):
    return 'Descriptor(%r, %r, %r, %r, %r, %r)' % (
        self.test_suite, self.measurement, self.bot, self.test_case,
        self.statistic, self.build_type)

  @classmethod
  def FromTestPath(cls, path):
    """Parse a test path into a Descriptor.

    Args:
      path: Array of strings of any length.

    Returns:
      Descriptor
    """
    if len(path) < 2:
      return cls()

    bot = path.pop(0) + ':' + path.pop(0)
    if len(path) == 0:
      return cls(bot=bot)

    test_suite = path.pop(0)

    if hashlib.sha256(test_suite).hexdigest() in PARTIAL_TEST_SUITE_HASHES:
      if len(path) == 0:
        return cls(bot=bot)
      test_suite += ':' + path.pop(0)

    if test_suite.startswith('resource_sizes '):
      test_suite = 'resource_sizes:' + test_suite[16:-1]
    else:
      for prefix in GROUPABLE_TEST_SUITE_PREFIXES:
        if test_suite.startswith(prefix):
          test_suite = prefix[:-1] + ':' + test_suite[len(prefix):]
          break

    if len(path) == 0:
      return cls(test_suite=test_suite, bot=bot)

    build_type = TEST_BUILD_TYPE
    measurement = path.pop(0)
    statistic = None
    # TODO(crbug.com/853258) some measurements include path[4]
    for suffix in STATISTICS:
      if measurement.endswith('_' + suffix):
        statistic = suffix
        measurement = measurement[:-(1 + len(suffix))]
    if len(path) == 0:
      return cls(test_suite=test_suite, bot=bot, measurement=measurement,
                 build_type=build_type, statistic=statistic)

    test_case = path.pop(0)
    if test_case.endswith('_ref'):
      test_case = test_case[:-4]
      build_type = REFERENCE_BUILD_TYPE
    if test_case == REFERENCE_BUILD_TYPE:
      build_type = REFERENCE_BUILD_TYPE
      test_case = None
    # TODO(crbug.com/853258) some test_cases include path[5] and/or path[6]
    # and/or path[7]
    # TODO(crbug.com/853258) some test_cases need to be modified

    return cls(test_suite=test_suite, bot=bot, measurement=measurement,
               statistic=statistic, test_case=test_case, build_type=build_type)

  def ToTestPaths(self):
    # There may be multiple possible test paths for a given Descriptor.

    if not self.bot:
      return []

    test_path = self.bot.replace(':', '/')
    if not self.test_suite:
      return [test_path]

    test_path += '/'

    if self.test_suite.startswith('resource_sizes:'):
      test_path += 'resource sizes (%s)' % self.test_suite[15:]
    elif (hashlib.sha256(self.test_suite).hexdigest() in
          COMPOSITE_TEST_SUITE_HASHES):
      test_path += self.test_suite.replace(':', '/')
    else:
      first_part = self.test_suite.split(':')[0]
      for prefix in GROUPABLE_TEST_SUITE_PREFIXES:
        if prefix[:-1] == first_part:
          test_path += prefix + self.test_suite[len(first_part) + 1:]
          break
      else:
        test_path += self.test_suite
    if not self.measurement:
      return [test_path]

    # TODO(crbug.com/853258) some measurements need to be modified
    test_path += '/' + self.measurement
    if self.statistic:
      test_path += '_' + self.statistic
    if self.test_case:
      # TODO(crbug.com/853258) some test_cases need to be modified
      test_path += '/' + self.test_case

    candidates = [test_path]
    if self.build_type == REFERENCE_BUILD_TYPE:
      candidates = [candidate + suffix
                    for candidate in candidates
                    for suffix in ['_ref', '/ref']]
    return candidates
