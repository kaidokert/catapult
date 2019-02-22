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
  def GenerateTestCases__RunSkipIfExpectedTest(cls, options):
    del options
    yield 'SkipIfExpectedTest', ()

  def _RunSkipTest(self):
    self.skipTest('SKIPPING TEST')

  def _RunSkipIfExpectedTest(self):
    cls = self.__class__
    expectation = (cls.typ_test_runner
                   .expectations
                   .expected_results_for('SkipIfExpectedTest'))
    if expectation == set(['FAIL']):
      self.skipTest('Skip is in the expectations'
                    ' for the test in new test'
                    ' expectations format')

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
