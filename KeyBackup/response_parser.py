#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import json

from example_data_provider import get_example_data

def _transform_to_byte_array(json_object):
    byte_array = bytearray(json_object[str(i)] for i in range(len(json_object)))
    return byte_array


def get_fmdn_shared_key(vault_keys):
    json_object = json.loads(vault_keys)

    for key in json_object:
        if key == "finder_hw":
            json_array = json_object[key]
            if not json_array:
                continue

            # Google's vault can hold multiple key generations ("epochs") for this
            # security domain if the account's FMDN owner key was ever rotated -
            # always take the newest one instead of whichever entry the array lists
            # first, or a stale/rotated-out epoch gets used and every decrypt against
            # current device data fails forever (see NovaApi's owner-key-version
            # mismatch error). The old code here unconditionally returned after the
            # first array entry and never compared epochs at all.
            latest = max(json_array, key=lambda item: int(item["epoch"]))
            print(f"[ResponseParser] Selected vault key epoch {latest['epoch']} (of {len(json_array)} available).")
            return _transform_to_byte_array(latest["key"])

    raise Exception("No suitable key found in the vault keys.")


if __name__ == '__main__':
    vault_keys = get_example_data("sample_vault_keys")
    print(get_fmdn_shared_key(vault_keys).hex())