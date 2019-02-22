# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys

from telemetry.testing import serially_executed_browser_test_case

class SkipTest(
    serially_executed_browser_test_case.SeriallyExecutedBrowserTestCase):

  @classmethod
  def GenerateTestCases__RunSkipTest(cls, options):
    del options
    yield 'SkipTest', ()

  def _RunSkipTest(self):
    self.skipTest('SKIPPING TEST')

  @classmethod
  def GenerateTestCases__RunPassTest(cls, options):
    del options
    yield 'PassTest', ()

  def _RunPassTest(self):
    pass

class SkipTestExpectationFiles(
    serially_executed_browser_test_case.SeriallyExecutedBrowserTestCase):

  @classmethod
  def GenerateTags(cls, finder_options, possible_browser):
    del finder_options, possible_browser
    return ['foo', 'bar']

  @classmethod
  def GenerateTestCases__RunSkipTest(cls, options):
    del options
    yield 'SkipTest', ()

  @classmethod
  def GenerateTestCases__RunSkipIfExpectedToFail(cls, options):
    del options
    yield 'SkipIfExpectedToFail', ()

  def _RunSkipTest(self):
    self.skipTest('SKIPPING TEST')

  def _RunSkipIfExpectedToFail(self):
    cls = self.__class__
    test_name = ('browser_tests.skip_tests_test.SkipTestExpectationFiles'
                 '.SkipIfExpectedToFail')
    expectation, _ = (cls.typ_test_runner
                      .expectations
                      .expectations_for(test_name))
    if expectation == set(['FAIL']):
      self.skipTest('Skipping test that is expected to fail')

  @classmethod
  def GenerateTestCases__RunPassTest(cls, options):
    del options
    yield 'PassTest', ()

  def _RunPassTest(self):
    pass

def load_tests(loader, tests, pattern):
  del loader, tests, pattern
  return serially_executed_browser_test_case.LoadAllTestsInModule(
      sys.modules[__name__])
