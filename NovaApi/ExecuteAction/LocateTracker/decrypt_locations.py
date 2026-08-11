#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import datetime
import hashlib

from Auth.token_cache import get_cached_values_with_prefix
from FMDNCrypto.foreign_tracker_cryptor import decrypt
from KeyBackup.cloud_key_decryptor import decrypt_eik, decrypt_aes_gcm
from NovaApi.ExecuteAction.LocateTracker.decrypted_location import WrappedLocation
from ProtoDecoders import DeviceUpdate_pb2
from ProtoDecoders import Common_pb2
from ProtoDecoders.DeviceUpdate_pb2 import DeviceRegistration
from ProtoDecoders.decoder import parse_device_update_protobuf
from SpotApi.CreateBleDevice.config import mcu_fast_pair_model_id
from SpotApi.CreateBleDevice.util import flip_bits
from SpotApi.GetEidInfoForE2eeDevices.get_eid_info_request import get_eid_info
from SpotApi.GetEidInfoForE2eeDevices.get_owner_key import get_owner_key, get_owner_key_from_wrapped_blob


def create_google_maps_link(latitude, longitude):
    try:  
        latitude = float(latitude)
        longitude = float(longitude)
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("Invalid latitude or longitude values.")
    except ValueError as e:
        return f"Error: {e}" #more descriptive error message for the user
    base_url = "https://www.google.com/maps/search/?api=1"
    query_params = f"query={latitude},{longitude}"  

    return f"{base_url}&{query_params}"

# Indicates if the device is a custom microcontroller
def is_mcu_tracker(device_registration: DeviceRegistration) -> bool:
    return device_registration.fastPairModelId == mcu_fast_pair_model_id


def retrieve_identity_key(device_registration: DeviceRegistration) -> bytes:
    is_mcu = is_mcu_tracker(device_registration)
    encrypted_user_secrets = device_registration.encryptedUserSecrets

    encrypted_identity_key = flip_bits(
        encrypted_user_secrets.encryptedIdentityKey,
        is_mcu)

    try:
        return decrypt_eik(get_owner_key(), encrypted_identity_key)
    except Exception:
        pass  # current owner key didn't decrypt this tracker's identity key - try the next fallback

    # The account-level "current" owner key (owner_key_version=-1) didn't decrypt
    # this tracker's identity key - retry by asking explicitly for the version the
    # tracker's own data says it needs, instead of trusting whatever "-1" happened
    # to resolve to. An account can have trackers on more than one owner key
    # generation; see SpotApi/GetEidInfoForE2eeDevices/get_owner_key.py.
    needed_version = encrypted_user_secrets.ownerKeyVersion
    try:
        return decrypt_eik(get_owner_key(owner_key_version=needed_version), encrypted_identity_key)
    except Exception:
        pass  # that version didn't work either - try the last-resort fallback below

    # Last resort: GetEidInfoForE2eeDevices always hands back its own idea of
    # "current" regardless of which version we ask it for (both attempts
    # above confirmed that empirically) - so try every owner-key blob fetched
    # directly from the real Find My Device web app's own API during sign-in
    # instead (see KeyBackup/vault_web_api.py). Each is still encrypted with
    # this account's one stable shared key; verified that unwrapping the
    # "current" version's blob this way reproduces the exact owner key the
    # normal path above already derives, so the same unwrap applied to every
    # other cached version is expected to yield each of those real keys too.
    for name, blob_hex in get_cached_values_with_prefix("encrypted_owner_key_v").items():
        try:
            owner_key = get_owner_key_from_wrapped_blob(bytes.fromhex(blob_hex))
            identity_key = decrypt_eik(owner_key, encrypted_identity_key)
            print(f"[DecryptLocations] Decrypted using {name}.")
            return identity_key
        except Exception:
            continue

    e2eeData = get_eid_info()
    current_owner_key_version = e2eeData.encryptedOwnerKeyAndMetadata.ownerKeyVersion

    print("")
    print("-" * 40)
    print("Attention:")
    print("-" * 40)

    if encrypted_user_secrets.ownerKeyVersion < current_owner_key_version:
        print(f"Failed to decrypt E2EE data. This tracker was encrypted with owner key version {encrypted_user_secrets.ownerKeyVersion}, but the current owner key version is {current_owner_key_version}.\nThis happens if you reset your end-to-end-encrypted data in the past.\nThe tracker cannot be decrypted anymore, and it is recommended to remove it in the Find My Device app.")
        exit(1)
    else:
        tried_versions = ", ".join(sorted(get_cached_values_with_prefix("encrypted_owner_key_v").keys())) or "none cached"
        print(f"Failed to decrypt identity key encrypted with owner key version {encrypted_user_secrets.ownerKeyVersion}, current owner key version is {current_owner_key_version}. Also retried by explicitly requesting owner key version {needed_version}, and by trying every vault key version fetched from the Find My Device web app during sign-in ({tried_versions}) - all failed to decrypt.\nThis may happen if the cached owner key is stale (e.g. after re-doing the Google sign-in). To resolve this issue, remove the 'owner_key' entry from 'Auth/secrets.json' so it gets re-derived, or delete the whole file to sign in again from scratch.")
        exit(1)


def decrypt_location_response_locations(device_update_protobuf):

    device_registration = device_update_protobuf.deviceMetadata.information.deviceRegistration

    identity_key = retrieve_identity_key(device_registration)
    locations_proto = device_update_protobuf.deviceMetadata.information.locationInformation.reports.recentLocationAndNetworkLocations
    is_mcu = is_mcu_tracker(device_registration)

    # At All Areas Reports or Own Reports
    recent_location = locations_proto.recentLocation
    recent_location_time = locations_proto.recentLocationTimestamp

    # High Traffic Reports
    network_locations = list(locations_proto.networkLocations)
    network_locations_time = list(locations_proto.networkLocationTimestamps)

    if locations_proto.HasField("recentLocation"):
        network_locations.append(recent_location)
        network_locations_time.append(recent_location_time)

    location_time_array = []
    for loc, time in zip(network_locations, network_locations_time):

        if loc.status == Common_pb2.Status.SEMANTIC:
            print("Semantic Location Report")

            wrapped_location = WrappedLocation(
                decrypted_location=b'',
                time=int(time.seconds),
                accuracy=0,
                status=loc.status,
                is_own_report=True,
                name=loc.semanticLocation.locationName
            )
            location_time_array.append(wrapped_location)
        else:

            encrypted_location = loc.geoLocation.encryptedReport.encryptedLocation
            public_key_random = loc.geoLocation.encryptedReport.publicKeyRandom

            if public_key_random == b"":  # Own Report
                identity_key_hash = hashlib.sha256(identity_key).digest()
                decrypted_location = decrypt_aes_gcm(identity_key_hash, encrypted_location)
            else:
                time_offset = 0 if is_mcu else loc.geoLocation.deviceTimeOffset
                decrypted_location = decrypt(identity_key, encrypted_location, public_key_random, time_offset)

            wrapped_location = WrappedLocation(
                decrypted_location=decrypted_location,
                time=int(time.seconds),
                accuracy=loc.geoLocation.accuracy,
                status=loc.status,
                is_own_report=loc.geoLocation.encryptedReport.isOwnReport,
                name=""
            )
            location_time_array.append(wrapped_location)

    print("-" * 40)
    print("[DecryptLocations] Decrypted Locations:")

    if not location_time_array:
        print("No locations found.")
        return

    for loc in location_time_array:

        if loc.status == Common_pb2.Status.SEMANTIC:
            print(f"Semantic Location: {loc.name}")

        else:
            proto_loc = DeviceUpdate_pb2.Location()
            proto_loc.ParseFromString(loc.decrypted_location)

            latitude = proto_loc.latitude / 1e7
            longitude = proto_loc.longitude / 1e7
            altitude = proto_loc.altitude

            print(f"Latitude: {latitude}")
            print(f"Longitude: {longitude}")
            print(f"Altitude: {altitude}")
            print(f"Google Maps Link: {create_google_maps_link(latitude, longitude)}")
            
        print(f"Time: {datetime.datetime.fromtimestamp(loc.time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Status: {loc.status}")
        print(f"Is Own Report: {loc.is_own_report}")
        print("-" * 40)

    pass


if __name__ == '__main__':
    res = parse_device_update_protobuf("")
    decrypt_location_response_locations(res)