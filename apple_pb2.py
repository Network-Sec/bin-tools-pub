# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: apple.proto
# Protobuf Python Version: 6.30.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    6,
    30,
    0,
    '',
    'apple.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0b\x61pple.proto\x12\x05\x61pple\"P\n\nWifiDevice\x12\r\n\x05\x62ssid\x18\x01 \x01(\t\x12&\n\x08location\x18\x02 \x01(\x0b\x32\x0f.apple.LocationH\x00\x88\x01\x01\x42\x0b\n\t_location\"\xad\x01\n\tAppleWLoc\x12\'\n\x0cwifi_devices\x18\x02 \x03(\x0b\x32\x11.apple.WifiDevice\x12-\n\x13\x63\x65ll_tower_response\x18\x16 \x03(\x0b\x32\x10.apple.CellTower\x12\x31\n\x12\x63\x65ll_tower_request\x18\x19 \x01(\x0b\x32\x10.apple.CellTowerH\x00\x88\x01\x01\x42\x15\n\x13_cell_tower_request\"\xb5\x01\n\tCellTower\x12\x0b\n\x03mcc\x18\x01 \x01(\r\x12\x0b\n\x03mnc\x18\x02 \x01(\r\x12\x0f\n\x07\x63\x65ll_id\x18\x03 \x01(\r\x12\x0e\n\x06tac_id\x18\x04 \x01(\r\x12&\n\x08location\x18\x05 \x01(\x0b\x32\x0f.apple.LocationH\x00\x88\x01\x01\x12\x13\n\x06uarfcn\x18\x06 \x01(\rH\x01\x88\x01\x01\x12\x10\n\x03pid\x18\x07 \x01(\rH\x02\x88\x01\x01\x42\x0b\n\t_locationB\t\n\x07_uarfcnB\x06\n\x04_pid\"\xe8\x01\n\x08Location\x12\x15\n\x08latitude\x18\x01 \x01(\x03H\x00\x88\x01\x01\x12\x16\n\tlongitude\x18\x02 \x01(\x03H\x01\x88\x01\x01\x12 \n\x13horizontal_accuracy\x18\x03 \x01(\x03H\x02\x88\x01\x01\x12\x15\n\x08\x61ltitude\x18\x05 \x01(\x03H\x03\x88\x01\x01\x12\x1e\n\x11vertical_accuracy\x18\x06 \x01(\x03H\x04\x88\x01\x01\x42\x0b\n\t_latitudeB\x0c\n\n_longitudeB\x16\n\x14_horizontal_accuracyB\x0b\n\t_altitudeB\x14\n\x12_vertical_accuracyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'apple_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_WIFIDEVICE']._serialized_start=22
  _globals['_WIFIDEVICE']._serialized_end=102
  _globals['_APPLEWLOC']._serialized_start=105
  _globals['_APPLEWLOC']._serialized_end=278
  _globals['_CELLTOWER']._serialized_start=281
  _globals['_CELLTOWER']._serialized_end=462
  _globals['_LOCATION']._serialized_start=465
  _globals['_LOCATION']._serialized_end=697
# @@protoc_insertion_point(module_scope)
