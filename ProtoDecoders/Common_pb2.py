# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ProtoDecoders/Common.proto
# Protobuf Python Version: 4.25.3
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1aProtoDecoders/Common.proto\"&\n\x04Time\x12\x0f\n\x07seconds\x18\x01 \x01(\r\x12\r\n\x05nanos\x18\x02 \x01(\r\"y\n\x0eLocationReport\x12+\n\x10semanticLocation\x18\x05 \x01(\x0b\x32\x11.SemanticLocation\x12!\n\x0bgeoLocation\x18\n \x01(\x0b\x32\x0c.GeoLocation\x12\x17\n\x06status\x18\x0b \x01(\x0e\x32\x07.Status\"(\n\x10SemanticLocation\x12\x14\n\x0clocationName\x18\x01 \x01(\t\"d\n\x0bGeoLocation\x12)\n\x0f\x65ncryptedReport\x18\x01 \x01(\x0b\x32\x10.EncryptedReport\x12\x18\n\x10\x64\x65viceTimeOffset\x18\x02 \x01(\r\x12\x10\n\x08\x61\x63\x63uracy\x18\x03 \x01(\x02\"Z\n\x0f\x45ncryptedReport\x12\x17\n\x0fpublicKeyRandom\x18\x01 \x01(\x0c\x12\x19\n\x11\x65ncryptedLocation\x18\x02 \x01(\x0c\x12\x13\n\x0bisOwnReport\x18\x03 \x01(\x08\"V\n\x1fGetEidInfoForE2eeDevicesRequest\x12\x17\n\x0fownerKeyVersion\x18\x01 \x01(\x05\x12\x1a\n\x12hasOwnerKeyVersion\x18\x02 \x01(\x08*H\n\x06Status\x12\x0c\n\x08SEMANTIC\x10\x00\x12\x0e\n\nLAST_KNOWN\x10\x01\x12\x10\n\x0c\x43ROWDSOURCED\x10\x02\x12\x0e\n\nAGGREGATED\x10\x03\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ProtoDecoders.Common_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_STATUS']._serialized_start=517
  _globals['_STATUS']._serialized_end=589
  _globals['_TIME']._serialized_start=30
  _globals['_TIME']._serialized_end=68
  _globals['_LOCATIONREPORT']._serialized_start=70
  _globals['_LOCATIONREPORT']._serialized_end=191
  _globals['_SEMANTICLOCATION']._serialized_start=193
  _globals['_SEMANTICLOCATION']._serialized_end=233
  _globals['_GEOLOCATION']._serialized_start=235
  _globals['_GEOLOCATION']._serialized_end=335
  _globals['_ENCRYPTEDREPORT']._serialized_start=337
  _globals['_ENCRYPTEDREPORT']._serialized_end=427
  _globals['_GETEIDINFOFORE2EEDEVICESREQUEST']._serialized_start=429
  _globals['_GETEIDINFOFORE2EEDEVICESREQUEST']._serialized_end=515
# @@protoc_insertion_point(module_scope)
