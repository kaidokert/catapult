# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: go.chromium.org/luci/cv/api/recipe/v1/cq.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='go.chromium.org/luci/cv/api/recipe/v1/cq.proto',
  package='cq.recipe',
  syntax='proto3',
  serialized_options=b'Z,go.chromium.org/luci/cv/api/recipe/v1;recipe',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n.go.chromium.org/luci/cv/api/recipe/v1/cq.proto\x12\tcq.recipe\"c\n\x05Input\x12\x0e\n\x06\x61\x63tive\x18\x01 \x01(\x08\x12\x0f\n\x07\x64ry_run\x18\x02 \x01(\x08\x12\x14\n\x0c\x65xperimental\x18\x03 \x01(\x08\x12\x11\n\ttop_level\x18\x04 \x01(\x08\x12\x10\n\x08run_mode\x18\x05 \x01(\t\"\xfb\x01\n\x06Output\x12\x1b\n\x13triggered_build_ids\x18\x01 \x03(\x03\x12&\n\x05retry\x18\x02 \x01(\x0e\x32\x17.cq.recipe.Output.Retry\x12&\n\x05reuse\x18\x03 \x03(\x0b\x32\x17.cq.recipe.Output.Reuse\x1a*\n\x05Reuse\x12\x13\n\x0bmode_regexp\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65ny\x18\x02 \x01(\x08\"X\n\x05Retry\x12\x1c\n\x18OUTPUT_RETRY_UNSPECIFIED\x10\x00\x12\x18\n\x14OUTPUT_RETRY_ALLOWED\x10\x01\x12\x17\n\x13OUTPUT_RETRY_DENIED\x10\x02\x42.Z,go.chromium.org/luci/cv/api/recipe/v1;recipeb\x06proto3'
)



_OUTPUT_RETRY = _descriptor.EnumDescriptor(
  name='Retry',
  full_name='cq.recipe.Output.Retry',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='OUTPUT_RETRY_UNSPECIFIED', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='OUTPUT_RETRY_ALLOWED', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='OUTPUT_RETRY_DENIED', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=326,
  serialized_end=414,
)
_sym_db.RegisterEnumDescriptor(_OUTPUT_RETRY)


_INPUT = _descriptor.Descriptor(
  name='Input',
  full_name='cq.recipe.Input',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='active', full_name='cq.recipe.Input.active', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='dry_run', full_name='cq.recipe.Input.dry_run', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='experimental', full_name='cq.recipe.Input.experimental', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='top_level', full_name='cq.recipe.Input.top_level', index=3,
      number=4, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='run_mode', full_name='cq.recipe.Input.run_mode', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
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
  serialized_start=61,
  serialized_end=160,
)


_OUTPUT_REUSE = _descriptor.Descriptor(
  name='Reuse',
  full_name='cq.recipe.Output.Reuse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='mode_regexp', full_name='cq.recipe.Output.Reuse.mode_regexp', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='deny', full_name='cq.recipe.Output.Reuse.deny', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
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
  serialized_start=282,
  serialized_end=324,
)

_OUTPUT = _descriptor.Descriptor(
  name='Output',
  full_name='cq.recipe.Output',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='triggered_build_ids', full_name='cq.recipe.Output.triggered_build_ids', index=0,
      number=1, type=3, cpp_type=2, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='retry', full_name='cq.recipe.Output.retry', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='reuse', full_name='cq.recipe.Output.reuse', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_OUTPUT_REUSE, ],
  enum_types=[
    _OUTPUT_RETRY,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=163,
  serialized_end=414,
)

_OUTPUT_REUSE.containing_type = _OUTPUT
_OUTPUT.fields_by_name['retry'].enum_type = _OUTPUT_RETRY
_OUTPUT.fields_by_name['reuse'].message_type = _OUTPUT_REUSE
_OUTPUT_RETRY.containing_type = _OUTPUT
DESCRIPTOR.message_types_by_name['Input'] = _INPUT
DESCRIPTOR.message_types_by_name['Output'] = _OUTPUT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Input = _reflection.GeneratedProtocolMessageType('Input', (_message.Message,), {
  'DESCRIPTOR' : _INPUT,
  '__module__' : 'go.chromium.org.luci.cv.api.recipe.v1.cq_pb2'
  # @@protoc_insertion_point(class_scope:cq.recipe.Input)
  })
_sym_db.RegisterMessage(Input)

Output = _reflection.GeneratedProtocolMessageType('Output', (_message.Message,), {

  'Reuse' : _reflection.GeneratedProtocolMessageType('Reuse', (_message.Message,), {
    'DESCRIPTOR' : _OUTPUT_REUSE,
    '__module__' : 'go.chromium.org.luci.cv.api.recipe.v1.cq_pb2'
    # @@protoc_insertion_point(class_scope:cq.recipe.Output.Reuse)
    })
  ,
  'DESCRIPTOR' : _OUTPUT,
  '__module__' : 'go.chromium.org.luci.cv.api.recipe.v1.cq_pb2'
  # @@protoc_insertion_point(class_scope:cq.recipe.Output)
  })
_sym_db.RegisterMessage(Output)
_sym_db.RegisterMessage(Output.Reuse)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
