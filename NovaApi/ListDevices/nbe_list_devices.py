#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import sys
import argparse
import binascii
from NovaApi.ExecuteAction.LocateTracker.location_request import get_location_data_for_device
from NovaApi.nova_request import nova_request
from NovaApi.scopes import NOVA_LIST_DEVICS_API_SCOPE
from NovaApi.util import generate_random_uuid
from ProtoDecoders import DeviceUpdate_pb2
from ProtoDecoders.decoder import parse_device_list_protobuf, get_canonic_ids
from SpotApi.CreateBleDevice.create_ble_device import register_esp32
from SpotApi.UploadPrecomputedPublicKeyIds.upload_precomputed_public_key_ids import refresh_custom_trackers


def request_device_list():

    hex_payload = create_device_list_request()
    result = nova_request(NOVA_LIST_DEVICS_API_SCOPE, hex_payload)

    return result


def create_device_list_request():
    wrapper = DeviceUpdate_pb2.DevicesListRequest()

    # Query for Spot devices
    wrapper.deviceListRequestPayload.type = DeviceUpdate_pb2.DeviceType.SPOT_DEVICE

    # Set a random UUID as the request ID
    wrapper.deviceListRequestPayload.id = generate_random_uuid()

    # Serialize to binary string
    binary_payload = wrapper.SerializeToString()

    # Convert to hex string
    hex_payload = binascii.hexlify(binary_payload).decode('utf-8')

    return hex_payload


def list_devices():
    print("Loading...")

    got_args = len(sys.argv) > 1
    parser = argparse.ArgumentParser()
    parser.add_argument('-add', '-a', dest='add', default=None, type=int, required=False, help='how many items to add')
    parser.add_argument('-query','-q', dest='query', default=None, type=str, required=False, help='query location by name, comma separated list')
    args = parser.parse_args()

    # talk to server
    result_hex = request_device_list()
    device_list = parse_device_list_protobuf(result_hex)
    refresh_custom_trackers(device_list)
    canonic_ids = get_canonic_ids(device_list)

    if got_args is False:
        # interactive mode
        print("")
        print("-" * 50)
        print("Welcome to GoogleFindMyTools!")
        print("-" * 50)
        print("")
        print("The following trackers are available:")

        for idx, (device_name, canonic_id) in enumerate(canonic_ids, start=1):
            print(f"{idx}. {device_name}: {canonic_id}")

        selected_value = input("\nIf you want to see locations of a tracker, type the number of the tracker and press 'Enter'.\nIf you want to register a new ESP32- or Zephyr-based tracker, type 'r' and press 'Enter': ")

        if selected_value == 'r':
            print("Loading...")
            register_esp32()
        else:
            selected_idx = int(selected_value) - 1
            selected_device_name = canonic_ids[selected_idx][0]
            selected_canonic_id = canonic_ids[selected_idx][1]

            get_location_data_for_device(selected_canonic_id, selected_device_name)
    else:
        # batch mode
        if args.add is not None:
            assert (args.add>0) and (args.add<1000), 'add argument out of range'
            for _ in range(args.add):
                register_esp32(batch_mode=True)

        if args.query is not None:
            # filter devices by name
            assert len(args.query)>0, 'name argument out of range'
            for nm in args.query.split(','):
                for device_name, canonic_id in canonic_ids:
                    if nm == device_name:
                        get_location_data_for_device(canonic_id, device_name, batch_mode=True)


if __name__ == '__main__':
    list_devices()
