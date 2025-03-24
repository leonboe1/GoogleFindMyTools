#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
import hashlib
from binascii import unhexlify
from concurrent.futures import ProcessPoolExecutor
import time
import pyscrypt

from example_data_provider import get_example_data


def ascii_to_bytes(string):
    return string.encode('ascii')


def get_lskf_hash(pin: str, salt: bytes) -> bytes:
    # Parameters
    data_to_hash = ascii_to_bytes(pin)  # Convert the string to an ASCII byte array

    log_n_cost = 4096  # CPU/memory cost parameter
    block_size = 8  # Block size
    parallelization = 1  # Parallelization factor
    key_length = 32  # Length of the derived key in bytes

    # Perform Scrypt hashing
    hashed = pyscrypt.hash(
        password=data_to_hash,
        salt=salt,
        N=log_n_cost,
        r=block_size,
        p=parallelization,
        dkLen=key_length
    )

    return hashed

def hash_pin(pin):
    sample_pin_salt = unhexlify(get_example_data("sample_pin_salt"))

    hash_object = hashlib.sha256(get_lskf_hash(pin, sample_pin_salt))
    hash_hex = hash_object.hexdigest()

    print(f"PIN: {pin}, Hash: {hash_hex}")
    return pin, hash_hex


if __name__ == '__main__':
    start_time = time.time()
    pins = [f"{i:04d}" for i in range(10000)]

    with ProcessPoolExecutor() as executor:
        results = list(executor.map(hash_pin, pins))

    for pin, hashed in results:
        print(f"PIN: {pin}, Hash: {hashed}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken: {elapsed_time:.2f} seconds")