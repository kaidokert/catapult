# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: go.chromium.org/luci/buildbucket/proto/notification.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='go.chromium.org/luci/buildbucket/proto/notification.proto',
  package='buildbucket.v2',
  syntax='proto3',
  serialized_options=b'Z4go.chromium.org/luci/buildbucket/proto;buildbucketpb',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n9go.chromium.org/luci/buildbucket/proto/notification.proto\x12\x0e\x62uildbucket.v2\x1a\x1fgoogle/protobuf/timestamp.proto\"r\n\x0cNotification\x12-\n\ttimestamp\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x0e\n\x06\x61pp_id\x18\x02 \x01(\t\x12\x10\n\x08\x62uild_id\x18\x03 \x01(\x03\x12\x11\n\tuser_data\x18\x04 \x01(\x0c\"=\n\x12NotificationConfig\x12\x14\n\x0cpubsub_topic\x18\x01 \x01(\t\x12\x11\n\tuser_data\x18\x02 \x01(\x0c\x42\x36Z4go.chromium.org/luci/buildbucket/proto;buildbucketpbb\x06proto3'
  ,
  dependencies=[google_dot_protobuf_dot_timestamp__pb2.DESCRIPTOR,])




_NOTIFICATION = _descriptor.Descriptor(
  name='Notification',
  full_name='buildbucket.v2.Notification',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='buildbucket.v2.Notification.timestamp', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='app_id', full_name='buildbucket.v2.Notification.app_id', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='build_id', full_name='buildbucket.v2.Notification.build_id', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='user_data', full_name='buildbucket.v2.Notification.user_data', index=3,
      number=4, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=110,
  serialized_end=224,
)


_NOTIFICATIONCONFIG = _descriptor.Descriptor(
  name='NotificationConfig',
  full_name='buildbucket.v2.NotificationConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='pubsub_topic', full_name='buildbucket.v2.NotificationConfig.pubsub_topic', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='user_data', full_name='buildbucket.v2.NotificationConfig.user_data', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=226,
  serialized_end=287,
)

_NOTIFICATION.fields_by_name['timestamp'].message_type = google_dot_protobuf_dot_timestamp__pb2._TIMESTAMP
DESCRIPTOR.message_types_by_name['Notification'] = _NOTIFICATION
DESCRIPTOR.message_types_by_name['NotificationConfig'] = _NOTIFICATIONCONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Notification = _reflection.GeneratedProtocolMessageType('Notification', (_message.Message,), {
  'DESCRIPTOR' : _NOTIFICATION,
  '__module__' : 'go.chromium.org.luci.buildbucket.proto.notification_pb2'
  # @@protoc_insertion_point(class_scope:buildbucket.v2.Notification)
  })
_sym_db.RegisterMessage(Notification)

NotificationConfig = _reflection.GeneratedProtocolMessageType('NotificationConfig', (_message.Message,), {
  'DESCRIPTOR' : _NOTIFICATIONCONFIG,
  '__module__' : 'go.chromium.org.luci.buildbucket.proto.notification_pb2'
  # @@protoc_insertion_point(class_scope:buildbucket.v2.NotificationConfig)
  })
_sym_db.RegisterMessage(NotificationConfig)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
