#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
from binascii import unhexlify

from Auth.token_cache import get_cached_value_or_set
from KeyBackup.cloud_key_decryptor import decrypt_owner_key
from KeyBackup.shared_key_retrieval import get_shared_key
from SpotApi.GetEidInfoForE2eeDevices.get_eid_info_request import get_eid_info

def _retrieve_owner_key(owner_key_version: int) -> str:
    eid_info = get_eid_info(owner_key_version)
    shared_key = get_shared_key()

    encrypted_owner_key = eid_info.encryptedOwnerKeyAndMetadata.encryptedOwnerKey
    owner_key = decrypt_owner_key(shared_key, encrypted_owner_key)
    returned_version = eid_info.encryptedOwnerKeyAndMetadata.ownerKeyVersion

    print(f"Retrieved owner key with version: {returned_version}")

    return owner_key.hex()


def get_owner_key_from_wrapped_blob(encrypted_owner_key: bytes) -> bytes:
    """Decrypts a specific owner-key blob (e.g. one fetched for a particular
    version via KeyBackup/vault_web_api.py, since GetEidInfoForE2eeDevices
    always hands back only its own idea of "current" regardless of what
    version is requested - confirmed empirically, see
    NovaApi/ExecuteAction/LocateTracker/decrypt_locations.py's retry chain)
    using the account's one stable shared key. Verified against this account:
    decrypting the "current" version's blob this way reproduces the exact
    owner key GetEidInfoForE2eeDevices's own default path already derives, so
    the same operation applied to a *different* version's blob is expected to
    yield that version's real owner key instead of guessing at request
    parameters the server evidently ignores."""
    return decrypt_owner_key(get_shared_key(), encrypted_owner_key)


def get_owner_key(owner_key_version: int = -1) -> bytes:
    # -1 (the default) means "whatever the account-level endpoint considers
    # current" - kept under the original flat 'owner_key' cache key for
    # backward compatibility. A specific version is cached separately, since
    # an account can have trackers on more than one owner key generation and
    # a single flat slot can only ever remember one answer (see
    # NovaApi/ExecuteAction/LocateTracker/decrypt_locations.py, which retries
    # with a specific version on a decrypt failure).
    cache_key = "owner_key" if owner_key_version == -1 else f"owner_key_v{owner_key_version}"
    return unhexlify(get_cached_value_or_set(cache_key, lambda: _retrieve_owner_key(owner_key_version)))


if __name__ == '__main__':
    print(get_owner_key())