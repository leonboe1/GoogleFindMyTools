#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

def flip_bits(data: bytes, enabled: bool) -> bytes:
    """Flips all bits in each byte of the given byte sequence."""
    if enabled:
        return bytes(b ^ 0xFF for b in data)

    return data


def hours_to_seconds(hours):
    return hours * 3600