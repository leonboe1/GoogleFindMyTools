#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import binascii
import subprocess

from google.protobuf import text_format
import datetime
import pytz

from ProtoDecoders import DeviceUpdate_pb2, LocationReportsUpload_pb2
from example_data_provider import get_example_data


# Custom message formatter to print the Protobuf byte fields as hex strings
def custom_message_formatter(message, indent, as_one_line):
    lines = []
    indent = f"{indent}"
    indent = indent.removeprefix("0")

    for field, value in message.ListFields():
        if field.type == field.TYPE_BYTES:
            hex_value = binascii.hexlify(value).decode('utf-8')
            lines.append(f"{indent}{field.name}: \"{hex_value}\"")
        elif field.type == field.TYPE_MESSAGE:
            if field.label == field.LABEL_REPEATED:
                for sub_message in value:
                    if field.message_type.name == "Time":
                        # Convert Unix time to human-readable format
                        unix_time = sub_message.seconds
                        local_time = datetime.datetime.fromtimestamp(unix_time, pytz.timezone('Europe/Berlin'))
                        lines.append(f"{indent}{field.name} {{\n{indent}  {local_time}\n{indent}}}")
                    else:
                        nested_message = custom_message_formatter(sub_message, f"{indent}  ", as_one_line)
                        lines.append(f"{indent}{field.name} {{\n{nested_message}\n{indent}}}")
            else:
                if field.message_type.name == "Time":
                    # Convert Unix time to human-readable format
                    unix_time = value.seconds
                    local_time = datetime.datetime.fromtimestamp(unix_time, pytz.timezone('Europe/Berlin'))
                    lines.append(f"{indent}{field.name} {{\n{indent}  {local_time}\n{indent}}}")
                else:
                    nested_message = custom_message_formatter(value, f"{indent}  ", as_one_line)
                    lines.append(f"{indent}{field.name} {{\n{nested_message}\n{indent}}}")
        else:
            lines.append(f"{indent}{field.name}: {value}")
    return "\n".join(lines)


def parse_location_report_upload_protobuf(hex_string):
    location_reports = LocationReportsUpload_pb2.LocationReportsUpload()
    location_reports.ParseFromString(bytes.fromhex(hex_string))
    return location_reports


def parse_device_update_protobuf(hex_string):
    device_update = DeviceUpdate_pb2.DeviceUpdate()
    device_update.ParseFromString(bytes.fromhex(hex_string))
    return device_update


def parse_device_list_protobuf(hex_string):
    device_list = DeviceUpdate_pb2.DevicesList()
    device_list.ParseFromString(bytes.fromhex(hex_string))
    return device_list


def get_last_seen(device) -> int | None:
    """Unix timestamp of when this device was last seen, matching what the
    real Find My Device web app shows for both device types, from whichever
    of two different underlying sources actually applies:
    - Phones: hardwareInfo.lastSeenTime (reverse engineered from a live
      account capture, cross-checked against the real web app's own data
      for the same device at the same moment - see DeviceHardwareInfo in
      DeviceUpdate.proto for the caveats). Spot/BLE tags never have this.
    - Spot/BLE tags (and phones too, as a fallback): the most recent
      location report's own timestamp - there's no hardware-status concept
      for a tag, so the web app uses "last reported a location" instead.
    None if neither is present.
    """
    if device.HasField("hardwareInfo") and device.hardwareInfo.HasField("lastSeenTime"):
        return device.hardwareInfo.lastSeenTime.seconds
    recent = device.information.locationInformation.reports.recentLocationAndNetworkLocations
    if recent.HasField("recentLocationTimestamp"):
        return recent.recentLocationTimestamp.seconds
    return None


def get_canonic_ids(device_list):
    result = []
    for device in device_list.deviceMetadata:
        if device.identifierInformation.type == DeviceUpdate_pb2.IDENTIFIER_ANDROID:
            canonic_ids = device.identifierInformation.phoneInformation.canonicIds.canonicId
        else:
            canonic_ids = device.identifierInformation.canonicIds.canonicId
        device_name = device.userDefinedDeviceName
        last_seen = get_last_seen(device)
        for canonic_id in canonic_ids:
            result.append((device_name, canonic_id.id, last_seen))
    return result


def print_location_report_upload_protobuf(hex_string):
    print(text_format.MessageToString(parse_location_report_upload_protobuf(hex_string), message_formatter=custom_message_formatter))


def print_device_update_protobuf(hex_string):
    print(text_format.MessageToString(parse_device_update_protobuf(hex_string), message_formatter=custom_message_formatter))


def print_device_list_protobuf(hex_string):
    print(text_format.MessageToString(parse_device_list_protobuf(hex_string), message_formatter=custom_message_formatter))


if __name__ == '__main__':
    # Recompile
    subprocess.run(["protoc", "--python_out=.", "ProtoDecoders/Common.proto"], cwd="../")
    subprocess.run(["protoc", "--python_out=.", "ProtoDecoders/DeviceUpdate.proto"], cwd="../")
    subprocess.run(["protoc", "--python_out=.", "ProtoDecoders/LocationReportsUpload.proto"], cwd="../")

    subprocess.run(["protoc", "--pyi_out=.", "ProtoDecoders/Common.proto"], cwd="../")
    subprocess.run(["protoc", "--pyi_out=.", "ProtoDecoders/DeviceUpdate.proto"], cwd="../")
    subprocess.run(["protoc", "--pyi_out=.", "ProtoDecoders/LocationReportsUpload.proto"], cwd="../")

    print("\n ------------------- \n")

    print("Device List: ")
    print_device_list_protobuf(get_example_data("sample_nbe_list_devices_response"))

    print("Own Report: ")
    print_location_report_upload_protobuf(get_example_data("sample_own_report"))

    print("\n ------------------- \n")

    print("Not Own Report: ")
    print_location_report_upload_protobuf(get_example_data("sample_foreign_report"))

    print("\n ------------------- \n")

    print("Device Update: ")
    print_device_update_protobuf(get_example_data("sample_device_update"))
