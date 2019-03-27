# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

""" Functions to write trace data in perfetto protobuf format.

This module makes use of neither python-protobuf library nor python classes
compiled from .proto definitions, because currently there's no way to
deploy those to all the places where telemetry is run.

Definitions of perfetto messages can be found here:
https://android.googlesource.com/platform/external/perfetto/+/refs/heads/master/protos/perfetto/trace/
"""

import encoder
import wire_format

from collections import defaultdict


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

# Timestamp of the last event from each thread. Used for delta-encoding
# of timestamps.
_last_timestamps = {}


class _TracePacket(object):
  def __init__(self):
    self.interned_data = None
    self.thread_descriptor = None
    self.incremental_state_cleared = None
    self.track_event = None
    self.trusted_packet_sequence_id = None

  def encode(self):
    parts = []
    if self.trusted_packet_sequence_id is not None:
      writer = encoder.UInt32Encoder(10, False, False)
      writer(parts.append, self.trusted_packet_sequence_id)
    if self.track_event is not None:
      tag = encoder.TagBytes(11, wire_format.WIRETYPE_LENGTH_DELIMITED)
      data = self.track_event.encode()
      length = encoder._VarintBytes(len(data))
      parts += [tag, length, data]
    if self.interned_data is not None:
      tag = encoder.TagBytes(12, wire_format.WIRETYPE_LENGTH_DELIMITED)
      data = self.interned_data.encode()
      length = encoder._VarintBytes(len(data))
      parts += [tag, length, data]
    if self.incremental_state_cleared is not None:
      writer = encoder.BoolEncoder(41, False, False)
      writer(parts.append, self.incremental_state_cleared)
    if self.thread_descriptor is not None:
      tag = encoder.TagBytes(44, wire_format.WIRETYPE_LENGTH_DELIMITED)
      data = self.thread_descriptor.encode()
      length = encoder._VarintBytes(len(data))
      parts += [tag, length, data]

    return b"".join(parts)


class _InternedData(object):
  def __init__(self):
    self.event_category = None
    self.legacy_event_name = None

  def encode(self):
    parts = []
    if self.event_category is not None:
      tag = encoder.TagBytes(1, wire_format.WIRETYPE_LENGTH_DELIMITED)
      data = self.event_category.encode()
      length = encoder._VarintBytes(len(data))
      parts += [tag, length, data]
    if self.legacy_event_name is not None:
      tag = encoder.TagBytes(2, wire_format.WIRETYPE_LENGTH_DELIMITED)
      data = self.legacy_event_name.encode()
      length = encoder._VarintBytes(len(data))
      parts += [tag, length, data]

    return b"".join(parts)


class _EventCategory(object):
  def __init__(self):
    self.iid = None
    self.name = None

  def encode(self):
    parts = []
    if self.iid is not None:
      writer = encoder.UInt32Encoder(1, False, False)
      writer(parts.append, self.iid)
    if self.name is not None:
      writer = encoder.StringEncoder(2, False, False)
      writer(parts.append, self.name)

    return b"".join(parts)


_LegacyEventName = _EventCategory


class _ThreadDescriptor(object):
  def __init__(self):
    self.pid = None
    self.tid = None
    self.reference_timestamp_us = None

  def encode(self):
    parts = []
    if self.pid is not None:
      writer = encoder.UInt32Encoder(1, False, False)
      writer(parts.append, self.pid)
    if self.tid is not None:
      writer = encoder.UInt32Encoder(2, False, False)
      writer(parts.append, self.tid)
    if self.reference_timestamp_us is not None:
      writer = encoder.Int64Encoder(6, False, False)
      writer(parts.append, self.reference_timestamp_us)

    return b"".join(parts)


class _TrackEvent(object):
  def __init__(self):
    self.timestamp_absolute_us = None
    self.timestamp_delta_us = None
    self.legacy_event = None
    self.category_iids = None

  def encode(self):
    parts = []
    if self.timestamp_delta_us is not None:
      writer = encoder.Int64Encoder(1, False, False)
      writer(parts.append, self.timestamp_delta_us)
    if self.category_iids is not None:
      writer = encoder.UInt32Encoder(3, True, False)
      writer(parts.append, self.category_iids)
    if self.legacy_event is not None:
      tag = encoder.TagBytes(6, wire_format.WIRETYPE_LENGTH_DELIMITED)
      data = self.legacy_event.encode()
      length = encoder._VarintBytes(len(data))
      parts += [tag, length, data]
    if self.timestamp_absolute_us is not None:
      writer = encoder.Int64Encoder(16, False, False)
      writer(parts.append, self.timestamp_absolute_us)

    return b"".join(parts)


class _LegacyEvent(object):
  def __init__(self):
    self.phase = None
    self.name_iid = None

  def encode(self):
    parts = []
    if self.name_iid is not None:
      writer = encoder.UInt32Encoder(1, False, False)
      writer(parts.append, self.name_iid)
    if self.phase is not None:
      writer = encoder.Int32Encoder(2, False, False)
      writer(parts.append, self.phase)

    return b"".join(parts)


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
    if trace_packet.interned_data is None:
      trace_packet.interned_data = _InternedData()
    trace_packet.interned_data.event_category = _EventCategory()
    trace_packet.interned_data.event_category.iid = categories[category]
    trace_packet.interned_data.event_category.name = category
  return categories[category]


def _intern_event_name(event_name, trace_packet, tid):
  global _interned_event_names_by_tid
  event_names = _interned_event_names_by_tid[tid]
  if event_name not in event_names:
    event_names[event_name] = len(event_names)
    if trace_packet.interned_data is None:
      trace_packet.interned_data = _InternedData()
    trace_packet.interned_data.legacy_event_name = _LegacyEventName()
    trace_packet.interned_data.legacy_event_name.iid = event_names[event_name]
    trace_packet.interned_data.legacy_event_name.name = event_name
  return event_names[event_name]


def _write_trace_packet(output, trace_packet):
  tag = encoder.TagBytes(1, wire_format.WIRETYPE_LENGTH_DELIMITED)
  output.write(tag)
  binary_data = trace_packet.encode()
  encoder._EncodeVarint(output.write, len(binary_data))
  output.write(binary_data)


def write_thread_descriptor_event(output, pid, tid, ts):
  """ Write the first event in a sequence.

  Call this function before writing any other events.
  Note that this function is NOT thread-safe.

  Args:
    output: a file-like object to write events into.
    pid: process ID.
    tid: thread ID.
    ts: timestamp in milliseconds.
  """
  global _last_timestamps
  ts_us = int(1000 * ts)
  _last_timestamps[tid] = ts_us

  thread_descriptor_packet = _TracePacket()
  thread_descriptor_packet.trusted_packet_sequence_id = _get_sequence_id(tid)
  thread_descriptor_packet.thread_descriptor = _ThreadDescriptor()
  thread_descriptor_packet.thread_descriptor.pid = pid
  # Thread ID from threading module doesn't fit into int32.
  # But we don't need the exact thread ID, just some number to
  # distinguish one thread from another. We assume that the last 31 bits
  # will do for that purpose.
  thread_descriptor_packet.thread_descriptor.tid = tid & 0x7FFFFFFF
  thread_descriptor_packet.thread_descriptor.reference_timestamp_us = ts_us
  thread_descriptor_packet.incremental_state_cleared = True;

  _write_trace_packet(output, thread_descriptor_packet)


def write_event(output, ph, category, name, ts, args, tid):
  """ Write a trace event.

  Note that this function is NOT thread-safe.

  Args:
    output: a file-like object to write events into.
    ph: phase of event.
    category: category of event.
    name: event name.
    ts: timestamp in milliseconds.
    args: this argument is currently ignored.
    tid: thread ID.
  """
  del args  # TODO(khokhlov): Encode args as DebugAnnotations.

  global _last_timestamps
  ts_us = int(1000 * ts)
  delta_ts = ts_us - _last_timestamps[tid]

  packet = _TracePacket()
  packet.trusted_packet_sequence_id = _get_sequence_id(tid)
  packet.track_event = _TrackEvent()

  if delta_ts >= 0:
    packet.track_event.timestamp_delta_us = delta_ts
    _last_timestamps[tid] = ts_us
  else:
    packet.track_event.timestamp_absolute_us = ts_us

  packet.track_event.category_iids = [_intern_category(category, packet, tid)]
  legacy_event = _LegacyEvent()
  legacy_event.phase = ord(ph)
  legacy_event.name_iid = _intern_event_name(name, packet, tid)
  packet.track_event.legacy_event = legacy_event
  _write_trace_packet(output, packet)

