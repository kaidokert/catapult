# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import logging
import sys

from telemetry import benchmark_runner
from telemetry.internal.util import binary_manager


_COMMANDS = {
    'list': benchmark_runner.List,
    'run': benchmark_runner.Run
}


def ArgumentParser(results_arg_parser=None):
  parser = argparse.ArgumentParser(description='Benchmark runner')
  subparsers = parser.add_subparsers(dest='command')
  subparsers.required = True
  subparsers.add_parser(
      'list',
      help='list benchmarks or stories',
      description='List available benchmarks or stories')
  subparsers.add_parser(
      'run',
      help='run a benchmark',
      description='Run a benchmark',
      parents=[results_arg_parser])
  # TODO: Other options should be migrated away from optparse and registered
  # here using argparse methods instead.
  return parser


def ParseArgs(args=None, environment=None, results_arg_parser=None):
  if args is None:
    args = sys.argv[1:]
  if len(args) > 0 and args[0] not in _COMMANDS:
    args.insert(0, 'run')  # Default command is run.

  # TODO: When optparse is gone, this should just call parse_args on the
  # fully formed parser as returned by.ArgumentParser.
  parser = ArgumentParser(results_arg_parser)
  parsed_args, unknown = parser.parse_known_args(args)

  # For now, we still need to create the optparse parser defined for the
  # selected command. Much of the following code is lifted from the
  # current telemetry.benchmark_runner.main function.
  binary_manager.InitDependencyManager(environment.client_configs)

  command = _COMMANDS[parsed_args.command]
  opt_parser = command.CreateParser()
  command.AddCommandLineArgs(opt_parser, environment)

  # Set the default chrome root variable.
  opt_parser.set_defaults(chrome_root=environment.default_chrome_root)

  options, positional_args = opt_parser.parse_args(unknown)
  options.positional_args = positional_args
  command.ProcessCommandLineArgs(opt_parser, options, environment)

  # Merge back our argparse args with the optparse options.
  for arg in vars(parsed_args):
    setattr(options, arg, getattr(parsed_args, arg))

  return options


def RunCommand(args):
  return_code = _COMMANDS[args.command]().Run(args)
  if return_code == -1:
    logging.warning('No stories were run.')
    return 0
  return return_code
