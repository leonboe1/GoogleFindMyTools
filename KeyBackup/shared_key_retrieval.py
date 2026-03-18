#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
from binascii import unhexlify

from Auth.token_cache import get_cached_value_or_set
from KeyBackup.shared_key_flow import request_shared_key_flow


def _retrieve_shared_key():
    print("""[SharedKeyRetrieval] You need to log in again to access end-to-end encrypted keys to decrypt location reports.
> This script will now open Google Chrome on your device.
> Make that you allow Python (or PyCharm) to control Chrome (macOS only).
    """)

    # Press enter to continue
    input("[SharedKeyRetrieval] Press 'Enter' to continue...")

    shared_key = request_shared_key_flow()

    if not shared_key:
        raise RuntimeError(
            "Shared key retrieval failed. Ensure Chrome/Chromium is installed "
            "and that you complete the Google sign-in flow."
        )

    return shared_key


def get_shared_key() -> bytes:
    return unhexlify(get_cached_value_or_set('shared_key', _retrieve_shared_key))


if __name__ == '__main__':
    print(get_shared_key())