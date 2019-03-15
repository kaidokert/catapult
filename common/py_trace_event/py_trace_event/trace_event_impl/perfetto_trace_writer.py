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


# TODO: Some comment to explain what it is.
# Preferably a link to perfetto trace format docs.
TRACE_PACKET_TAG = 10

# dicts of strings for interning
_categories = {} 
_event_names = {}

def _intern_category(category, trace_packet):
  global _categories
  if category not in _categories:
    _categories[category] = len(_categories)
    interned_category = trace_packet.interned_data.event_categories.add()
    interned_category.iid = _categories[category]
    interned_category.name = category
  return _categories[category]


def _intern_event_name(event_name, trace_packet):
  global _event_names
  if event_name not in _event_names:
    _event_names[event_name] = len(_event_names)
    interned_event_name = trace_packet.interned_data.legacy_event_names.add()
    interned_event_name.iid = _event_names[event_name]
    interned_event_name.name = event_name
  return _event_names[event_name]

def _write_trace_packet(output, trace_packet):
  binary_data = trace_packet.SerializeToString()
  _EncodeVarint(output.write, TRACE_PACKET_TAG)
  _EncodeVarint(output.write, len(binary_data))
  output.write(binary_data)
  #print packet

def write_thread_descriptor_event(output, pid, tid):
  thread_descriptor_packet = perfetto_proto_module.TracePacket()
  thread_descriptor_packet.thread_descriptor.pid = pid
  # FIXME: tid doesn't fit into int32!
  thread_descriptor_packet.thread_descriptor.tid = tid & 0x7FFFFFFF
  _write_trace_packet(output, thread_descriptor_packet)

def write_event(output, ph, category, name, ts, args):
  del args # FIXME: what to do with args?
  packet = perfetto_proto_module.TracePacket()
  packet.track_event.timestamp_absolute_us = int(1000 * ts)
  packet.track_event.legacy_event.phase = ord(ph)
  packet.track_event.category_iids.append(_intern_category(category, packet))
  packet.track_event.legacy_event.name_iid = _intern_event_name(name, packet)
  _write_trace_packet(output, packet)

def perfetto_proto_imported():
  return perfetto_proto_module is not None

