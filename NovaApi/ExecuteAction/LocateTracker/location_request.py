#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import asyncio

from Auth.fcm_receiver import FcmReceiver
from NovaApi.ExecuteAction.LocateTracker.decrypt_locations import decrypt_location_response_locations
from NovaApi.ExecuteAction.nbe_execute_action import create_action_request, serialize_action_request
from NovaApi.nova_request import nova_request
from NovaApi.scopes import NOVA_ACTION_API_SCOPE
from NovaApi.util import generate_random_uuid
from ProtoDecoders import DeviceUpdate_pb2
from ProtoDecoders.decoder import parse_device_update_protobuf
from example_data_provider import get_example_data

def create_location_request(canonic_device_id, fcm_registration_id, request_uuid):

    action_request = create_action_request(canonic_device_id, fcm_registration_id, request_uuid=request_uuid)

    # Random values, can be arbitrary
    action_request.action.locateTracker.lastHighTrafficEnablingTime.seconds = 1732120060
    action_request.action.locateTracker.contributorType = DeviceUpdate_pb2.SpotContributorType.FMDN_ALL_LOCATIONS

    # Convert to hex string
    hex_payload = serialize_action_request(action_request)

    return hex_payload


def get_location_data_for_device(canonic_device_id, name, batch_mode=False):

    print(f"[LocationRequest] Requesting location data for {name}...")

    result = None
    request_uuid = generate_random_uuid()

    def handle_location_response(response):
        nonlocal result
        device_update = parse_device_update_protobuf(response)

        if device_update.fcmMetadata.requestUuid == request_uuid:
            print("[LocationRequest] Location request successful. Decrypting locations...")
            result = parse_device_update_protobuf(response)
            #print_device_update_protobuf(response)

    fcm_token = FcmReceiver().register_for_location_updates(handle_location_response)

    hex_payload = create_location_request(canonic_device_id, fcm_token, request_uuid)
    nova_request(NOVA_ACTION_API_SCOPE, hex_payload)

    while result is None:
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.1))

    decrypt_location_response_locations(result, batch_mode=batch_mode)

if __name__ == '__main__':
    get_location_data_for_device(get_example_data("sample_canonic_device_id"), "Test")
