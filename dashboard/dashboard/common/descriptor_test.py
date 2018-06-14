# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from dashboard.common import descriptor


class DescriptorTest(unittest.TestCase):

  def testParseTestPath_Empty(self):
    desc = descriptor.Descriptor.ParseTestPath([])
    self.assertEqual(None, desc.test_suite)
    self.assertEqual(None, desc.measurement)
    self.assertEqual(None, desc.bot)
    self.assertEqual(None, desc.test_case)
    self.assertEqual(None, desc.statistic)
    self.assertEqual(None, desc.build_type)

  def testParseTestPath_Short(self):
    desc = descriptor.Descriptor.ParseTestPath([''])
    self.assertEqual(None, desc.test_suite)
    self.assertEqual(None, desc.measurement)
    self.assertEqual(None, desc.bot)
    self.assertEqual(None, desc.test_case)
    self.assertEqual(None, desc.statistic)
    self.assertEqual(None, desc.build_type)

  def testParseTestPath_Bot(self):
    desc = descriptor.Descriptor.ParseTestPath(['master', 'bot'])
    self.assertEqual(None, desc.test_suite)
    self.assertEqual(None, desc.measurement)
    self.assertEqual('master:bot', desc.bot)
    self.assertEqual(None, desc.test_case)
    self.assertEqual(None, desc.statistic)
    self.assertEqual(None, desc.build_type)

  def testParseTestPath_Suite(self):
    desc = descriptor.Descriptor.ParseTestPath(['master', 'bot', 'suite'])
    self.assertEqual('suite', desc.test_suite)
    self.assertEqual(None, desc.measurement)
    self.assertEqual('master:bot', desc.bot)
    self.assertEqual(None, desc.test_case)
    self.assertEqual(None, desc.statistic)
    self.assertEqual(None, desc.build_type)

  def testParseTestPath_Measurement(self):
    desc = descriptor.Descriptor.ParseTestPath([
        'master', 'bot', 'suite', 'measure'])
    self.assertEqual('suite', desc.test_suite)
    self.assertEqual('measure', desc.measurement)
    self.assertEqual('master:bot', desc.bot)
    self.assertEqual(None, desc.test_case)
    self.assertEqual(None, desc.statistic)
    self.assertEqual(descriptor.TEST_BUILD_TYPE, desc.build_type)

  def testParseTestPath_Statistic(self):
    desc = descriptor.Descriptor.ParseTestPath([
        'master', 'bot', 'suite', 'measure_avg'])
    self.assertEqual('suite', desc.test_suite)
    self.assertEqual('measure', desc.measurement)
    self.assertEqual('master:bot', desc.bot)
    self.assertEqual(None, desc.test_case)
    self.assertEqual('avg', desc.statistic)
    self.assertEqual(descriptor.TEST_BUILD_TYPE, desc.build_type)

  def testParseTestPath_Ref(self):
    desc = descriptor.Descriptor.ParseTestPath([
        'master', 'bot', 'suite', 'measure_avg', 'ref'])
    self.assertEqual('suite', desc.test_suite)
    self.assertEqual('measure', desc.measurement)
    self.assertEqual('master:bot', desc.bot)
    self.assertEqual(None, desc.test_case)
    self.assertEqual('avg', desc.statistic)
    self.assertEqual(descriptor.REFERENCE_BUILD_TYPE, desc.build_type)

  def testParseTestPath_TestCase(self):
    desc = descriptor.Descriptor.ParseTestPath([
        'master', 'bot', 'suite', 'measure_avg', 'case'])
    self.assertEqual('suite', desc.test_suite)
    self.assertEqual('measure', desc.measurement)
    self.assertEqual('master:bot', desc.bot)
    self.assertEqual('case', desc.test_case)
    self.assertEqual('avg', desc.statistic)
    self.assertEqual(descriptor.TEST_BUILD_TYPE, desc.build_type)

  def testParseTestPath_All(self):
    desc = descriptor.Descriptor.ParseTestPath([
        'master', 'bot', 'suite', 'measure_avg', 'case_ref'])
    self.assertEqual('suite', desc.test_suite)
    self.assertEqual('measure', desc.measurement)
    self.assertEqual('master:bot', desc.bot)
    self.assertEqual('case', desc.test_case)
    self.assertEqual('avg', desc.statistic)
    self.assertEqual(descriptor.REFERENCE_BUILD_TYPE, desc.build_type)

  def testCompileTestPaths_Empty(self):
    self.assertEqual([], descriptor.Descriptor().CompileTestPaths())

  def testCompileTestPaths_Bot(self):
    self.assertEqual(['master/bot'], descriptor.Descriptor(
        bot='master:bot').CompileTestPaths())

  def testCompileTestPaths_Suite(self):
    self.assertEqual(['master/bot/suite'], descriptor.Descriptor(
        bot='master:bot',
        test_suite='suite').CompileTestPaths())

  def testCompileTestPaths_Measurement(self):
    self.assertEqual(['master/bot/suite/measure'], descriptor.Descriptor(
        bot='master:bot',
        test_suite='suite',
        measurement='measure').CompileTestPaths())

  def testCompileTestPaths_Statistic(self):
    self.assertEqual(['master/bot/suite/measure_avg'], descriptor.Descriptor(
        bot='master:bot',
        test_suite='suite',
        measurement='measure',
        statistic='avg').CompileTestPaths())

  def testCompileTestPaths_Ref(self):
    test_path = 'master/bot/suite/measure'
    expected = [test_path + '_ref', test_path + '/ref']
    self.assertEqual(expected, descriptor.Descriptor(
        bot='master:bot',
        test_suite='suite',
        measurement='measure',
        build_type=descriptor.REFERENCE_BUILD_TYPE).CompileTestPaths())

  def testCompileTestPaths_TestCase(self):
    self.assertEqual(['master/bot/suite/measure/case'], descriptor.Descriptor(
        bot='master:bot',
        test_suite='suite',
        measurement='measure',
        test_case='case').CompileTestPaths())

  def testCompileTestPaths_All(self):
    test_path = 'master/bot/suite/measure_avg/case'
    expected = [test_path + '_ref', test_path + '/ref']
    self.assertEqual(expected, descriptor.Descriptor(
        bot='master:bot',
        test_suite='suite',
        measurement='measure',
        test_case='case',
        statistic='avg',
        build_type=descriptor.REFERENCE_BUILD_TYPE).CompileTestPaths())


if __name__ == '__main__':
  unittest.main()
