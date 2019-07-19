# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import optparse
import os
import sys
import unittest

import mock

from telemetry.command_line import parser
from telemetry.core import util
from telemetry import project_config


class ParserExit(Exception):
  pass


class ParserError(Exception):
  pass


class ParseArgsTests(unittest.TestCase):
  def setUp(self):
    # TODO(crbug.com/981349): Ideally parsing args should not have any side
    # effects; for now we need to mock out calls to set up logging and binary
    # manager.
    mock.patch('telemetry.command_line.parser.logging').start()
    mock.patch('telemetry.command_line.parser.binary_manager').start()

    mock.patch.object(
        argparse.ArgumentParser, 'exit', side_effect=ParserExit).start()
    mock.patch.object(
        optparse.OptionParser, 'exit', side_effect=ParserExit).start()
    self._argparse_error = mock.patch.object(
        argparse.ArgumentParser, 'error', side_effect=ParserError).start()
    self._optparse_error = mock.patch.object(
        optparse.OptionParser, 'error', side_effect=ParserError).start()

    examples_dir = os.path.join(util.GetTelemetryDir(), 'examples')
    self.config = project_config.ProjectConfig(
        top_level_dir=examples_dir,
        benchmark_dirs=[os.path.join(examples_dir, 'benchmarks')])

  def tearDown(self):
    mock.patch.stopall()

  def testHelpFlag(self):
    with self.assertRaises(ParserExit):
      parser.ParseArgs(['--help'], self.config)
    self.assertIn('Command line tool to run performance benchmarks.',
                  sys.stdout.getvalue())

  def testHelpCommand(self):
    with self.assertRaises(ParserExit):
      parser.ParseArgs(['help', 'run'], self.config)
    self.assertIn('To get help about a command use', sys.stdout.getvalue())

  def testRunHelp(self):
    with self.assertRaises(ParserExit):
      parser.ParseArgs(['run', '--help'], self.config)
    self.assertIn('--browser=BROWSER_TYPE', sys.stdout.getvalue())

  def testRunBenchmarkHelp(self):
    with self.assertRaises(ParserExit):
      parser.ParseArgs(['tbm_sample.tbm_sample', '--help'], self.config)
    self.assertIn('--browser=BROWSER_TYPE', sys.stdout.getvalue())

  def testListBenchmarks(self):
    args = parser.ParseArgs(['list', '--json', 'output.json'], self.config)
    self.assertEqual(args.command, 'list')
    self.assertEqual(args.json_filename, 'output.json')

  def testRunBenchmark(self):
    args = parser.ParseArgs([
        'run', 'tbm_sample.tbm_sample', '--browser=stable'], self.config)
    self.assertEqual(args.command, 'run')
    self.assertEqual(args.positional_args, ['tbm_sample.tbm_sample'])
    self.assertEqual(args.browser_type, 'stable')

  def testRunCommandIsDefault(self):
    args = parser.ParseArgs([
        'tbm_sample.tbm_sample', '--browser', 'stable'], self.config)
    self.assertEqual(args.command, 'run')
    self.assertEqual(args.positional_args, ['tbm_sample.tbm_sample'])
    self.assertEqual(args.browser_type, 'stable')

  def testRunCommandBenchmarkNameAtEnd(self):
    args = parser.ParseArgs([
        '--browser', 'stable', 'tbm_sample.tbm_sample'], self.config)
    self.assertEqual(args.command, 'run')
    self.assertEqual(args.positional_args, ['tbm_sample.tbm_sample'])
    self.assertEqual(args.browser_type, 'stable')

  def testRunBenchmark_UnknownBenchmark(self):
    with self.assertRaises(ParserError):
      parser.ParseArgs(
          ['run', 'foo.benchmark', '--browser=stable'], self.config)
    self._optparse_error.assert_called_with(
        'no such benchmark: foo.benchmark')

  def testRunBenchmark_MissingBenchmark(self):
    with self.assertRaises(ParserError):
      parser.ParseArgs(['run', '--browser=stable'], self.config)
    self._optparse_error.assert_called_with(
        'missing required argument: benchmark_name')

  def testRunBenchmark_TooManyArgs(self):
    with self.assertRaises(ParserError):
      parser.ParseArgs(
          ['run', 'tbm_sample.tbm_sample', 'other', '--browser=beta', 'args'],
          self.config)
    self._optparse_error.assert_called_with(
        'unrecognized arguments: other args')

  def testRunBenchmark_UnknownArg(self):
    with self.assertRaises(ParserError):
      parser.ParseArgs(
          ['run', 'tbm_sample.tbm_sample', '--non-existent-option'],
          self.config)
    self._optparse_error.assert_called_with(
        'no such option: --non-existent-option')

  def testRunBenchmark_ExternalOption(self):
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('--extra-special-option', action='store_true')

    args = parser.ParseArgs(
        ['run', 'tbm_sample.tbm_sample', '--extra-special-option'],
        self.config, results_arg_parser=my_parser)
    self.assertEqual(args.command, 'run')
    self.assertEqual(args.positional_args, ['tbm_sample.tbm_sample'])
    self.assertTrue(args.extra_special_option)

  def testListBenchmarks_NoExternalOptions(self):
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('--extra-special-option', action='store_true')

    with self.assertRaises(ParserError):
      # Listing benchmarks does not require the external results processor.
      parser.ParseArgs(
          ['list', '--extra-special-option'],
          self.config, results_arg_parser=my_parser)
    self._optparse_error.assert_called_with(
        'no such option: --extra-special-option')
