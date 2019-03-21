# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

try:
  from google.protobuf.internal.encoder import _EncodeVarint
  import perfetto_trace_pb2 as perfetto_proto_module
except:
  import traceback
  traceback.print_exc()
  perfetto_proto_module = None

from collections import defaultdict


# This is a header that precedes every TracePacket in a trace.
# The value is actually a field number 1 with a length-delimited
# wire type. See
# https://developers.google.com/protocol-buffers/docs/encoding#structure
# for details of protobuf encoding.
TRACE_PACKET_TAG = '\x0A'

# Dicts of strings for interning.
# Note that each thread has its own interning index.
_interned_categories_by_tid = defaultdict(dict)
_interned_event_names_by_tid = defaultdict(dict)

# Trusted sequence ids from telemetry should not overlap with
# trusted sequence ids from other trace producers. Chrome assigns
# sequence ids incrementally starting from 1 and we expect all its ids
# to be well below 10000. Starting from 2^20 will give us enough
# confidence that it will not overlap.
_next_sequence_id = 1<<20
_sequence_ids = {}


def _get_sequence_id(tid):
  global _sequence_ids
  global _next_sequence_id
  if tid not in _sequence_ids:
    _sequence_ids[tid] = _next_sequence_id
    _next_sequence_id += 1
  return _sequence_ids[tid]


def _intern_category(category, trace_packet, tid):
  global _interned_categories_by_tid
  categories = _interned_categories_by_tid[tid]
  if category not in categories:
    categories[category] = len(categories)
    interned_category = trace_packet.interned_data.event_categories.add()
    interned_category.iid = categories[category]
    interned_category.name = category
  return categories[category]


def _intern_event_name(event_name, trace_packet, tid):
  global _interned_event_names_by_tid
  event_names = _interned_event_names_by_tid[tid]
  if event_name not in event_names:
    event_names[event_name] = len(event_names)
    interned_event_name = trace_packet.interned_data.legacy_event_names.add()
    interned_event_name.iid = event_names[event_name]
    interned_event_name.name = event_name
  return event_names[event_name]


def _write_trace_packet(output, trace_packet, tid):
  trace_packet.trusted_packet_sequence_id = _get_sequence_id(tid)

  output.write(TRACE_PACKET_TAG)
  binary_data = trace_packet.SerializeToString()
  _EncodeVarint(output.write, len(binary_data))
  output.write(binary_data)


def write_thread_descriptor_event(output, pid, tid):
  thread_descriptor_packet = perfetto_proto_module.TracePacket()
  thread_descriptor_packet.thread_descriptor.pid = pid
  # TODO(khokhlov): tid doesn't fit into int32!
  thread_descriptor_packet.thread_descriptor.tid = tid & 0x7FFFFFFF
  thread_descriptor_packet.incremental_state_cleared = True;

  _write_trace_packet(output, thread_descriptor_packet, tid)


def write_event(output, ph, category, name, ts, args, tid):
  del args # TODO(khokhlov): encode args as DebugAnnotations
  packet = perfetto_proto_module.TracePacket()
  # TODO(khokhlov): implement delta timestamps
  packet.track_event.timestamp_absolute_us = int(1000 * ts)
  packet.track_event.legacy_event.phase = ord(ph)
  packet.track_event.category_iids.append(_intern_category(category, packet, tid))
  packet.track_event.legacy_event.name_iid = _intern_event_name(name, packet, tid)
  _write_trace_packet(output, packet, tid)


def perfetto_proto_imported():
  return perfetto_proto_module is not None

