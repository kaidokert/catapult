# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import mock

from telemetry.command_line import parser


class ParserExit(Exception):
  pass

class ParseArgsTests(unittest.TestCase):
  def setUp(self):
    # TODO(crbug.com/981349): Ideally parsing args should not have any side
    # effects; for now we need to mock out calls to set up logging and binary
    # manager.
    mock.patch('telemetry.command_line.parser.logging').start()
    mock.patch('telemetry.command_line.parser.binary_manager').start()

    self._parser_exit = mock.patch(argparse.ArgumentParser, 'exit').start()
    self._parser_exit.side_effect = ParserExit

  def tearDown(self):
    mock.patch.stopall()

  def testHelpFlag(self):
    with self.assertRaises(ParserExit):
      parser.ParseArgs(['--help'])
