# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: dashboard/protobuf/sheriff_config.proto

import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()

from dashboard.protobuf import sheriff_pb2 as dashboard_dot_protobuf_dot_sheriff__pb2

DESCRIPTOR = _descriptor.FileDescriptor(
    name='dashboard/protobuf/sheriff_config.proto',
    package='dashboard',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=_b(
        '\n\'dashboard/protobuf/sheriff_config.proto\x12\tdashboard\x1a dashboard/protobuf/sheriff.proto\"\xe5\x01\n\x0cMatchRequest\x12\x0c\n\x04path\x18\x01 \x01(\t\x12*\n\x05stats\x18\x02 \x03(\x0e\x32\x1b.dashboard.Pattern.StatType\x12\x36\n\x08metadata\x18\x03 \x01(\x0b\x32$.dashboard.MatchRequest.TestMetadata\x1a\x63\n\x0cTestMetadata\x12\r\n\x05units\x18\x01 \x01(\t\x12\x0e\n\x06master\x18\x02 \x01(\t\x12\x0b\n\x03\x62ot\x18\x03 \x01(\t\x12\x11\n\tbenchmark\x18\x04 \x01(\t\x12\x14\n\x0cmetric_parts\x18\x05 \x03(\t\"\xc2\x01\n\rMatchResponse\x12\x44\n\rsubscriptions\x18\x01 \x03(\x0b\x32-.dashboard.MatchResponse.SubscriptionMetadata\x1ak\n\x14SubscriptionMetadata\x12\x12\n\nconfig_set\x18\x01 \x01(\t\x12\x10\n\x08revision\x18\x02 \x01(\t\x12-\n\x0csubscription\x18\x03 \x01(\x0b\x32\x17.dashboard.Subscription\"%\n\x0bListRequest\x12\x16\n\x0eidentity_email\x18\x01 \x01(\t\"\xc0\x01\n\x0cListResponse\x12\x43\n\rsubscriptions\x18\x01 \x03(\x0b\x32,.dashboard.ListResponse.SubscriptionMetadata\x1ak\n\x14SubscriptionMetadata\x12\x12\n\nconfig_set\x18\x01 \x01(\t\x12\x10\n\x08revision\x18\x02 \x01(\t\x12-\n\x0csubscription\x18\x03 \x01(\x0b\x32\x17.dashboard.Subscriptionb\x06proto3'
    ),
    dependencies=[
        dashboard_dot_protobuf_dot_sheriff__pb2.DESCRIPTOR,
    ])

_MATCHREQUEST_TESTMETADATA = _descriptor.Descriptor(
    name='TestMetadata',
    full_name='dashboard.MatchRequest.TestMetadata',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='units',
            full_name='dashboard.MatchRequest.TestMetadata.units',
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode('utf-8'),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='master',
            full_name='dashboard.MatchRequest.TestMetadata.master',
            index=1,
            number=2,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode('utf-8'),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='bot',
            full_name='dashboard.MatchRequest.TestMetadata.bot',
            index=2,
            number=3,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode('utf-8'),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='benchmark',
            full_name='dashboard.MatchRequest.TestMetadata.benchmark',
            index=3,
            number=4,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode('utf-8'),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='metric_parts',
            full_name='dashboard.MatchRequest.TestMetadata.metric_parts',
            index=4,
            number=5,
            type=9,
            cpp_type=9,
            label=3,
            has_default_value=False,
            default_value=[],
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=219,
    serialized_end=318,
)

_MATCHREQUEST = _descriptor.Descriptor(
    name='MatchRequest',
    full_name='dashboard.MatchRequest',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='path',
            full_name='dashboard.MatchRequest.path',
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode('utf-8'),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='stats',
            full_name='dashboard.MatchRequest.stats',
            index=1,
            number=2,
            type=14,
            cpp_type=8,
            label=3,
            has_default_value=False,
            default_value=[],
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='metadata',
            full_name='dashboard.MatchRequest.metadata',
            index=2,
            number=3,
            type=11,
            cpp_type=10,
            label=1,
            has_default_value=False,
            default_value=None,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
    ],
    extensions=[],
    nested_types=[
        _MATCHREQUEST_TESTMETADATA,
    ],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=89,
    serialized_end=318,
)

_MATCHRESPONSE_SUBSCRIPTIONMETADATA = _descriptor.Descriptor(
    name='SubscriptionMetadata',
    full_name='dashboard.MatchResponse.SubscriptionMetadata',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='config_set',
            full_name='dashboard.MatchResponse.SubscriptionMetadata.config_set',
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode('utf-8'),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='revision',
            full_name='dashboard.MatchResponse.SubscriptionMetadata.revision',
            index=1,
            number=2,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode('utf-8'),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='subscription',
            full_name='dashboard.MatchResponse.SubscriptionMetadata.subscription',
            index=2,
            number=3,
            type=11,
            cpp_type=10,
            label=1,
            has_default_value=False,
            default_value=None,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=408,
    serialized_end=515,
)

_MATCHRESPONSE = _descriptor.Descriptor(
    name='MatchResponse',
    full_name='dashboard.MatchResponse',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='subscriptions',
            full_name='dashboard.MatchResponse.subscriptions',
            index=0,
            number=1,
            type=11,
            cpp_type=10,
            label=3,
            has_default_value=False,
            default_value=[],
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
    ],
    extensions=[],
    nested_types=[
        _MATCHRESPONSE_SUBSCRIPTIONMETADATA,
    ],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=321,
    serialized_end=515,
)

_LISTREQUEST = _descriptor.Descriptor(
    name='ListRequest',
    full_name='dashboard.ListRequest',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='identity_email',
            full_name='dashboard.ListRequest.identity_email',
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode('utf-8'),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=517,
    serialized_end=554,
)

_LISTRESPONSE_SUBSCRIPTIONMETADATA = _descriptor.Descriptor(
    name='SubscriptionMetadata',
    full_name='dashboard.ListResponse.SubscriptionMetadata',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='config_set',
            full_name='dashboard.ListResponse.SubscriptionMetadata.config_set',
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode('utf-8'),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='revision',
            full_name='dashboard.ListResponse.SubscriptionMetadata.revision',
            index=1,
            number=2,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode('utf-8'),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='subscription',
            full_name='dashboard.ListResponse.SubscriptionMetadata.subscription',
            index=2,
            number=3,
            type=11,
            cpp_type=10,
            label=1,
            has_default_value=False,
            default_value=None,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=408,
    serialized_end=515,
)

_LISTRESPONSE = _descriptor.Descriptor(
    name='ListResponse',
    full_name='dashboard.ListResponse',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='subscriptions',
            full_name='dashboard.ListResponse.subscriptions',
            index=0,
            number=1,
            type=11,
            cpp_type=10,
            label=3,
            has_default_value=False,
            default_value=[],
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR),
    ],
    extensions=[],
    nested_types=[
        _LISTRESPONSE_SUBSCRIPTIONMETADATA,
    ],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=557,
    serialized_end=749,
)

_MATCHREQUEST_TESTMETADATA.containing_type = _MATCHREQUEST
_MATCHREQUEST.fields_by_name[
    'stats'].enum_type = dashboard_dot_protobuf_dot_sheriff__pb2._PATTERN_STATTYPE
_MATCHREQUEST.fields_by_name[
    'metadata'].message_type = _MATCHREQUEST_TESTMETADATA
_MATCHRESPONSE_SUBSCRIPTIONMETADATA.fields_by_name[
    'subscription'].message_type = dashboard_dot_protobuf_dot_sheriff__pb2._SUBSCRIPTION
_MATCHRESPONSE_SUBSCRIPTIONMETADATA.containing_type = _MATCHRESPONSE
_MATCHRESPONSE.fields_by_name[
    'subscriptions'].message_type = _MATCHRESPONSE_SUBSCRIPTIONMETADATA
_LISTRESPONSE_SUBSCRIPTIONMETADATA.fields_by_name[
    'subscription'].message_type = dashboard_dot_protobuf_dot_sheriff__pb2._SUBSCRIPTION
_LISTRESPONSE_SUBSCRIPTIONMETADATA.containing_type = _LISTRESPONSE
_LISTRESPONSE.fields_by_name[
    'subscriptions'].message_type = _LISTRESPONSE_SUBSCRIPTIONMETADATA
DESCRIPTOR.message_types_by_name['MatchRequest'] = _MATCHREQUEST
DESCRIPTOR.message_types_by_name['MatchResponse'] = _MATCHRESPONSE
DESCRIPTOR.message_types_by_name['ListRequest'] = _LISTREQUEST
DESCRIPTOR.message_types_by_name['ListResponse'] = _LISTRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

MatchRequest = _reflection.GeneratedProtocolMessageType(
    'MatchRequest',
    (_message.Message,),
    dict(
        TestMetadata=_reflection.GeneratedProtocolMessageType(
            'TestMetadata',
            (_message.Message,),
            dict(
                DESCRIPTOR=_MATCHREQUEST_TESTMETADATA,
                __module__='dashboard.protobuf.sheriff_config_pb2'
                # @@protoc_insertion_point(class_scope:dashboard.MatchRequest.TestMetadata)
            )),
        DESCRIPTOR=_MATCHREQUEST,
        __module__='dashboard.protobuf.sheriff_config_pb2'
        # @@protoc_insertion_point(class_scope:dashboard.MatchRequest)
    ))
_sym_db.RegisterMessage(MatchRequest)
_sym_db.RegisterMessage(MatchRequest.TestMetadata)

MatchResponse = _reflection.GeneratedProtocolMessageType(
    'MatchResponse',
    (_message.Message,),
    dict(
        SubscriptionMetadata=_reflection.GeneratedProtocolMessageType(
            'SubscriptionMetadata',
            (_message.Message,),
            dict(
                DESCRIPTOR=_MATCHRESPONSE_SUBSCRIPTIONMETADATA,
                __module__='dashboard.protobuf.sheriff_config_pb2'
                # @@protoc_insertion_point(class_scope:dashboard.MatchResponse.SubscriptionMetadata)
            )),
        DESCRIPTOR=_MATCHRESPONSE,
        __module__='dashboard.protobuf.sheriff_config_pb2'
        # @@protoc_insertion_point(class_scope:dashboard.MatchResponse)
    ))
_sym_db.RegisterMessage(MatchResponse)
_sym_db.RegisterMessage(MatchResponse.SubscriptionMetadata)

ListRequest = _reflection.GeneratedProtocolMessageType(
    'ListRequest',
    (_message.Message,),
    dict(
        DESCRIPTOR=_LISTREQUEST,
        __module__='dashboard.protobuf.sheriff_config_pb2'
        # @@protoc_insertion_point(class_scope:dashboard.ListRequest)
    ))
_sym_db.RegisterMessage(ListRequest)

ListResponse = _reflection.GeneratedProtocolMessageType(
    'ListResponse',
    (_message.Message,),
    dict(
        SubscriptionMetadata=_reflection.GeneratedProtocolMessageType(
            'SubscriptionMetadata',
            (_message.Message,),
            dict(
                DESCRIPTOR=_LISTRESPONSE_SUBSCRIPTIONMETADATA,
                __module__='dashboard.protobuf.sheriff_config_pb2'
                # @@protoc_insertion_point(class_scope:dashboard.ListResponse.SubscriptionMetadata)
            )),
        DESCRIPTOR=_LISTRESPONSE,
        __module__='dashboard.protobuf.sheriff_config_pb2'
        # @@protoc_insertion_point(class_scope:dashboard.ListResponse)
    ))
_sym_db.RegisterMessage(ListResponse)
_sym_db.RegisterMessage(ListResponse.SubscriptionMetadata)

# @@protoc_insertion_point(module_scope)
