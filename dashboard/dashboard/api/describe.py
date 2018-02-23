# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import hashlib
import json
import logging

from dashboard.api import api_auth
from dashboard.api import api_request_handler
from dashboard.api import test_suites as test_suites_module
from dashboard.common import utils
from dashboard.models import graph_data
from google.appengine.api import memcache


PARTIAL_TEST_SUITE_HASHES = [
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
]


class DescribeHandler(api_request_handler.ApiRequestHandler):

  def get(self, test_suite):
    self._PreGet()
    suite_name, test_part1_name = self._SuiteName(test_suite)
    if not self._CanAccess(suite_name):
      self.response.write(json.dumps({
          'measurements': [],
          'bots': [],
          'test_cases': [],
      }))
      return

    cache_key = self._CacheKey(test_suite)
    cached = memcache.get(cache_key)
    if cached is not None:
      self.response.write(cached)
      return

    descriptor = json.dumps(self._Describe(suite_name, test_part1_name))
    self.response.write(descriptor)
    memcache.add(cache_key, descriptor, time=60*60*24)

  def _PreGet(self):
    try:
      api_auth.AuthorizeOauthUser()
    except (api_auth.OAuthError, api_auth.NotLoggedInError):
      # If the user isn't signed in or isn't an internal user, then they won't
      # be able to access internal_only timeseries, but they should still be
      # able to access non-internal_only timeseries.
      pass
    self._SetCorsHeadersIfAppropriate()

  @staticmethod
  def _SuiteName(test_suite):
    parts = test_suite.split(':')
    if DescribeHandler._IsPartialTestSuite(test_suite):
      return parts
    if test_suite.startswith('resource_sizes:'):
      return 'resource_sizes (%s)' % parts[1], None
    for prefix in test_suites_module.GROUPABLE_TEST_SUITE_PREFIXES:
      if parts[0] == prefix[:-1]:
        return prefix + ':'.join(parts[1:]), None
    return test_suite, None

  @staticmethod
  def _IsPartialTestSuite(test_suite):
    sha = hashlib.sha256(bytes(test_suite)).hexdigest()
    return sha in PARTIAL_TEST_SUITE_HASHES

  @staticmethod
  def _CanAccess(suite_name):
    query = graph_data.TestMetadata.query()
    query = query.filter(graph_data.TestMetadata.suite_name == suite_name)
    query = query.filter(graph_data.TestMetadata.parent_test == None)
    query = query.filter(graph_data.TestMetadata.deprecated == False)
    if not utils.IsInternalUser():
      query = query.filter(graph_data.TestMetadata.internal_only == False)
    return len(query.fetch(keys_only=True)) > 0

  @staticmethod
  def _CacheKey(test_suite):
    return 'api_describe_' + test_suite

  @staticmethod
  def _Describe(suite_name, test_part1_name):
    measurements = set()
    bots = set()
    test_cases = set()
    for key in DescribeHandler._FetchTestKeys(suite_name, test_part1_name):
      test_path = utils.TestPath(key)
      if test_path.endswith('_ref') or test_path.endswith('/ref'):
        continue
      test_path = test_path.split('/')
      bot = test_path[0] + ':' + test_path[1]
      bots.add(bot)
      test_path = test_path[3:]
      if test_part1_name:
        test_path = test_path[1:]
      measurement, test_case = DescribeHandler._Parse(
          test_path, suite_name, test_part1_name)
      measurements.add(measurement)
      if test_case:
        test_cases.add(test_case)

    return {
        'measurements': list(sorted(measurements)),
        'bots': list(sorted(bots)),
        'test_cases': list(sorted(test_cases)),
    }

  @staticmethod
  def _FetchTestKeys(suite_name, test_part1_name=None):
    query = graph_data.TestMetadata.query()
    query = query.filter(graph_data.TestMetadata.suite_name == suite_name)
    if test_part1_name:
      query = query.filter(
          graph_data.TestMetadata.test_part1_name == test_part1_name)
    query = query.filter(graph_data.TestMetadata.has_rows == True)
    query = query.filter(graph_data.TestMetadata.deprecated == False)
    if not utils.IsInternalUser():
      query = query.filter(graph_data.TestMetadata.internal_only == False)
    return query.fetch(keys_only=True)

  @staticmethod
  def _Parse(parts, suite_name, test_part1_name):
    if len(parts) == 1:
      return parts[0], None

    if suite_name.startswith('system_health'):
      if len(parts) == 2:
        return parts[0], None
      return parts[0], parts[2].replace('_', ':')

    if len(parts) == 2:
      return parts

    logging.info('unable to parse "%s" in %s/%s',
                 '/'.join(parts), suite_name, test_part1_name)
    return parts[0], ':'.join(parts[1:])
