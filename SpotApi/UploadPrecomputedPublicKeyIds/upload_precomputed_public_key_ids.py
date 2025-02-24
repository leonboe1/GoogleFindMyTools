#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
import time

from FMDNCrypto.eid_generator import ROTATION_PERIOD, generate_eid
from NovaApi.ExecuteAction.LocateTracker.decrypt_locations import retrieve_identity_key, is_mcu_tracker
from ProtoDecoders.DeviceUpdate_pb2 import DevicesList, UploadPrecomputedPublicKeyIdsRequest, PublicKeyIdList
from SpotApi.CreateBleDevice.config import max_truncated_eid_seconds_server
from SpotApi.CreateBleDevice.util import hours_to_seconds
from SpotApi.spot_request import spot_request


def refresh_custom_trackers(device_list: DevicesList):

    request = UploadPrecomputedPublicKeyIdsRequest()
    needs_upload = False

    for device in device_list.deviceMetadata:

        # This is a microcontroller
        if is_mcu_tracker(device.information.deviceRegistration):

            needs_upload = True

            new_truncated_ids = UploadPrecomputedPublicKeyIdsRequest.DevicePublicKeyIds()
            new_truncated_ids.pairDate = device.information.deviceRegistration.pairDate
            new_truncated_ids.canonicId.id = device.identifierInformation.canonicIds.canonicId[0].id

            identity_key = retrieve_identity_key(device.information.deviceRegistration)
            next_eids = get_next_eids(identity_key, new_truncated_ids.pairDate, int(time.time() - hours_to_seconds(3)), duration_seconds=max_truncated_eid_seconds_server)

            for next_eid in next_eids:
                new_truncated_ids.clientList.publicKeyIdInfo.append(next_eid)

            request.deviceEids.append(new_truncated_ids)

    if needs_upload:
        print("[UploadPrecomputedPublicKeyIds] Updating your registered µC devices...")
        try:
            bytes_data = request.SerializeToString()
            spot_request("UploadPrecomputedPublicKeyIds", bytes_data)
        except Exception as e:
            print(f"[UploadPrecomputedPublicKeyIds] Failed to refresh custom trackers. Please file a bug report. Continuing... {str(e)}")


def get_next_eids(eik: bytes, pair_date: int, start_date: int, duration_seconds: int) -> list[PublicKeyIdList.PublicKeyIdInfo]:
    duration_seconds = int(duration_seconds)
    public_key_id_list = []

    start_offset = start_date - pair_date
    current_time_offset = start_offset - (start_offset % ROTATION_PERIOD)

    static_eid = generate_eid(eik, 0)

    while current_time_offset <= start_offset + duration_seconds:
        time = pair_date + current_time_offset

        info = PublicKeyIdList.PublicKeyIdInfo()
        info.timestamp.seconds = time
        info.publicKeyId.truncatedEid = static_eid[:10]

        public_key_id_list.append(info)

        current_time_offset += 1024

    return public_key_id_list