# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: ProtoDecoders/DeviceUpdate.proto
# Protobuf Python Version: 5.28.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    2,
    '',
    'ProtoDecoders/DeviceUpdate.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from ProtoDecoders import Common_pb2 as ProtoDecoders_dot_Common__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n ProtoDecoders/DeviceUpdate.proto\x1a\x1aProtoDecoders/Common.proto\"1\n\x0c\x44\x65viceUpdate\x12!\n\x08metadata\x18\x03 \x01(\x0b\x32\x0f.DeviceMetadata\"M\n\x0e\x44\x65viceMetadata\x12\'\n\x0binformation\x18\x04 \x01(\x0b\x32\x12.DeviceInformation\x12\x12\n\ndeviceName\x18\x05 \x01(\t\"h\n\x11\x44\x65viceInformation\x12\x31\n\x13locationInformation\x18\x02 \x01(\x0b\x32\x14.LocationInformation\x12 \n\x05owner\x18\x03 \x01(\x0b\x32\x11.OwnerInformation\"F\n\x13LocationInformation\x12/\n\x07reports\x18\x03 \x01(\x0b\x32\x1e.LocationsAndTimestampsWrapper\"n\n\x1dLocationsAndTimestampsWrapper\x12M\n!recentLocationAndNetworkLocations\x18\x04 \x01(\x0b\x32\".RecentLocationAndNetworkLocations\"\x95\x02\n!RecentLocationAndNetworkLocations\x12\x38\n\x0erecentLocation\x18\x01 \x01(\x0b\x32 .LocationStatusAndRotationOffset\x12&\n\x17recentLocationTimestamp\x18\x02 \x01(\x0b\x32\x05.Time\x12:\n\x10networkLocations\x18\x05 \x03(\x0b\x32 .LocationStatusAndRotationOffset\x12(\n\x19networkLocationTimestamps\x18\x06 \x03(\x0b\x32\x05.Time\x12(\n minLocationsNeededForAggregation\x18\t \x01(\r\"{\n\x1fLocationStatusAndRotationOffset\x12?\n\x1blocationAndDeviceTimeOffset\x18\n \x01(\x0b\x32\x1a.LocationAndRotationOffset\x12\x17\n\x06status\x18\x0b \x01(\x0e\x32\x07.Status\"!\n\x10OwnerInformation\x12\r\n\x05\x65mail\x18\x01 \x01(\t*H\n\x06Status\x12\x0c\n\x08SEMANTIC\x10\x00\x12\x0e\n\nLAST_KNOWN\x10\x01\x12\x10\n\x0c\x43ROWDSOURCED\x10\x02\x12\x0e\n\nAGGREGATED\x10\x03\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ProtoDecoders.DeviceUpdate_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_STATUS']._serialized_start=924
  _globals['_STATUS']._serialized_end=996
  _globals['_DEVICEUPDATE']._serialized_start=64
  _globals['_DEVICEUPDATE']._serialized_end=113
  _globals['_DEVICEMETADATA']._serialized_start=115
  _globals['_DEVICEMETADATA']._serialized_end=192
  _globals['_DEVICEINFORMATION']._serialized_start=194
  _globals['_DEVICEINFORMATION']._serialized_end=298
  _globals['_LOCATIONINFORMATION']._serialized_start=300
  _globals['_LOCATIONINFORMATION']._serialized_end=370
  _globals['_LOCATIONSANDTIMESTAMPSWRAPPER']._serialized_start=372
  _globals['_LOCATIONSANDTIMESTAMPSWRAPPER']._serialized_end=482
  _globals['_RECENTLOCATIONANDNETWORKLOCATIONS']._serialized_start=485
  _globals['_RECENTLOCATIONANDNETWORKLOCATIONS']._serialized_end=762
  _globals['_LOCATIONSTATUSANDROTATIONOFFSET']._serialized_start=764
  _globals['_LOCATIONSTATUSANDROTATIONOFFSET']._serialized_end=887
  _globals['_OWNERINFORMATION']._serialized_start=889
  _globals['_OWNERINFORMATION']._serialized_end=922
# @@protoc_insertion_point(module_scope)
