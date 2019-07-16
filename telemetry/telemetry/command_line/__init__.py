# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from telemetry.command_line.parser import ParseArgs
from telemetry.command_line.parser import RunCommand


def main(environment):
  args = ParseArgs(environment=environment)
  return RunCommand(args)
