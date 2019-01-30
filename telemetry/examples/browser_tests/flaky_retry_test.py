# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys

from telemetry.testing import serially_executed_browser_test_case


class GetFlakyRetryCountTest(
    serially_executed_browser_test_case.SeriallyExecutedBrowserTestCase):
  _retry_count = 0

  @classmethod
  def GenerateTags(cls, finder_options, possible_browser):
    del finder_options, possible_browser
    return ['foo', 'bar']

  @classmethod
  def GenerateTestCases__RunFlakyTest(cls, options):
    del options
    yield 'FlakyTest', ()


  def GetFlakyRetryCount(self):
    return 3

  def _RunFlakyTest(self):
    if self.__class__._retry_count == self.GetFlakyRetryCount():
        return
    self.__class__._retry_count += 1
    self.fail()


class SetFlakyRetryCountTest(
    serially_executed_browser_test_case.SeriallyExecutedBrowserTestCase):
  _retry_count = -1

  @classmethod
  def GenerateTags(cls, finder_options, possible_browser):
    del finder_options, possible_browser
    return ['foo', 'bar']

  @classmethod
  def GenerateTestCases__RunFlakyTest(cls, options):
    del options
    yield 'FlakyTest', ()


  def SetFlakyRetryCount(self, retry_count):
    self.__class__._retry_count = retry_count

  def _RunFlakyTest(self):
    if self.__class__._retry_count == 1:
        return
    self.__class__._retry_count -= 1
    self.fail()


def load_tests(loader, tests, pattern):
  del loader, tests, pattern
  return serially_executed_browser_test_case.LoadAllTestsInModule(
      sys.modules[__name__])
