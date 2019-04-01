# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

""" Trace file formats
"""

# Legacy format: json list of events.
# Events can be written from multiple processes, but since no process
# can be sure that it is the last one, nobody writes the closing ']'.
# So the resulting file is not technically correct json.
JSON = "json"

# Full json with events and metadata.
# This format produces correct json ready to feed into TraceDataBuilder.
# Note that it is the responsibility of the user of py_trace_event to make sure
# that trace_disable() is called after all child processes have finished.
JSON_WITH_METADATA = "json_with_metadata"

# Perfetto protobuf trace format.
PROTOBUF = "protobuf"

