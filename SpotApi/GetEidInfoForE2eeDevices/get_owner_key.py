#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
from binascii import unhexlify

from Auth.token_cache import get_cached_value_or_set
from KeyBackup.cloud_key_decryptor import decrypt_owner_key
from KeyBackup.shared_key_retrieval import get_shared_key
from SpotApi.GetEidInfoForE2eeDevices.get_eid_info_request import get_eid_info

def _retrieve_owner_key():
    eid_info = get_eid_info()
    shared_key = get_shared_key()

    encrypted_owner_key = eid_info.encryptedOwnerKeyAndMetadata.encryptedOwnerKey.hex()
    owner_key = decrypt_owner_key(unhexlify(shared_key), encrypted_owner_key)

    return owner_key.hex()


def get_owner_key():
    return get_cached_value_or_set('owner_key', _retrieve_owner_key)


if __name__ == '__main__':
    print(get_owner_key())