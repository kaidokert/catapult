# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""DEPRECATED: Clients should import telemetry.command_line instead.
"""

from telemetry import command_line
from telemetry.command_line import commands


main = command_line.main
GetBenchmarkByName = commands.GetBenchmarkByName
