#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import threading

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


def get_location_data_for_device(canonic_device_id, name, timeout=60):

    print(f"[LocationRequest] Requesting location data for {name}...")

    result = None
    received = threading.Event()
    request_uuid = generate_random_uuid()
    receiver = FcmReceiver()

    def handle_location_response(response):
        nonlocal result
        device_update = parse_device_update_protobuf(response)

        if device_update.fcmMetadata.requestUuid == request_uuid:
            print("[LocationRequest] Location request successful. Decrypting locations...")
            result = device_update
            #print_device_update_protobuf(response)
            received.set()

    fcm_token = receiver.register_for_location_updates(handle_location_response)

    try:
        hex_payload = create_location_request(canonic_device_id, fcm_token, request_uuid)
        nova_request(NOVA_ACTION_API_SCOPE, hex_payload)

        # Google's push doesn't always come back (device offline, no fresh fix
        # available, etc.) - this used to poll forever with no way out, hanging
        # the whole script until it was killed by hand.
        if not received.wait(timeout=timeout):
            print(f"[LocationRequest] Timed out after {timeout}s waiting for {name}.")
            return

        decrypt_location_response_locations(result)
    finally:
        receiver.unregister_callback(handle_location_response)

if __name__ == '__main__':
    get_location_data_for_device(get_example_data("sample_canonic_device_id"), "Test")