#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
from ProtoDecoders import Common_pb2
from ProtoDecoders import DeviceUpdate_pb2
from SpotApi.spot_request import spot_request

def get_eid_info(owner_key_version: int = -1):
    # owner_key_version=-1 (the default) asks for whatever the account-level
    # endpoint considers "current" - which, for accounts with more than one
    # owner key generation in play, isn't reliably the version a *specific*
    # tracker's own data actually needs. Pass the tracker's own
    # encryptedUserSecrets.ownerKeyVersion here to ask for that version
    # explicitly instead of guessing.
    get_eid_info_for_e2ee_devices_request = Common_pb2.GetEidInfoForE2eeDevicesRequest()
    get_eid_info_for_e2ee_devices_request.ownerKeyVersion = owner_key_version
    get_eid_info_for_e2ee_devices_request.hasOwnerKeyVersion = True

    serialized_request = get_eid_info_for_e2ee_devices_request.SerializeToString()
    response_bytes = spot_request("GetEidInfoForE2eeDevices", serialized_request)

    eid_info = DeviceUpdate_pb2.GetEidInfoForE2eeDevicesResponse()
    eid_info.ParseFromString(response_bytes)

    return eid_info


if __name__ == '__main__':
    print(get_eid_info().encryptedOwnerKeyAndMetadata)