#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
from binascii import unhexlify

from Auth.token_cache import get_cached_value_or_set
from KeyBackup.cloud_key_decryptor import decrypt_owner_key
from KeyBackup.shared_key_retrieval import get_shared_key
from SpotApi.GetEidInfoForE2eeDevices.get_eid_info_request import get_eid_info

def _retrieve_owner_key() -> str:
    eid_info = get_eid_info()
    shared_key = get_shared_key()

    encrypted_owner_key = eid_info.encryptedOwnerKeyAndMetadata.encryptedOwnerKey
    owner_key = decrypt_owner_key(shared_key, encrypted_owner_key)
    owner_key_version = eid_info.encryptedOwnerKeyAndMetadata.ownerKeyVersion

    print(f"Retrieved owner key with version: {owner_key_version}")

    return owner_key.hex()


def get_owner_key() -> bytes:
    return unhexlify(get_cached_value_or_set('owner_key', _retrieve_owner_key))


if __name__ == '__main__':
    print(get_owner_key())