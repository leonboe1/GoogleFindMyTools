from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from binascii import unhexlify
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from TitanBackup.lskf_hasher import ascii_to_bytes, get_lskf_hash
from private import sample_pin, sample_pin_salt, sample_encrypted_recovery_key, sample_encrypted_application_key, \
    sample_encrypted_security_domain_key, sample_encrypted_shared_key

# Constants
VERSION = b'\x02\x00'
SECUREBOX = b'SECUREBOX'
SHARED_HKDF_AES_GCM = b'SHARED HKDF-SHA-256 AES-128-GCM'
P256_HKDF_AES_GCM = b'P256 HKDF-SHA-256 AES-128-GCM'


def derive_key_using_hkdf_sha256(input_key: bytes, salt: bytes, info: bytes) -> bytes:

    # Create 16-byte HKDF instance
    hkdf = HKDF(
        algorithm=SHA256(),
        length=16,
        salt=salt,
        info=info,
        backend=default_backend(),
    )

    # Derive key using HKDF
    return hkdf.derive(input_key)


def decrypt_aes_gcm_with_derived_key(encrypted_key: bytes, key: bytes, key_type_string: bytes,
                                     derive_with_public_key=False) -> bytes:

    # Only supporting specified version, else return
    if len(encrypted_key) < 2 or encrypted_key[:2] != VERSION:
        raise ValueError("Invalid version or data length")

    version_length = len(VERSION)

    # Get ciphertext and iv from encrypted key data
    ciphertext_offset = 65 if derive_with_public_key else 0
    ciphertext_and_iv = encrypted_key[version_length + ciphertext_offset:]

    # Create HKDF salt and info
    hkdf_salt = SECUREBOX + VERSION
    hkdf_info = P256_HKDF_AES_GCM if derive_with_public_key else SHARED_HKDF_AES_GCM

    if derive_with_public_key:
        # Perform key exchange and derive shared secret
        shared_public_key = encrypted_key[version_length:version_length + ciphertext_offset]
        key = derive_shared_secret(key, shared_public_key)

    # Derive key using HKDF
    derived_key = derive_key_using_hkdf_sha256(key, hkdf_salt, hkdf_info)

    # Decrypt data with AES-GCM
    return decrypt_aes_gcm(derived_key, ciphertext_and_iv, key_type_string)


def derive_shared_secret(private_key_jwt, public_key_bytes):

    # Extract EC private curve from JWT format
    private_key_bytes = private_key_jwt[:32]
    private_key = ec.derive_private_key(int.from_bytes(private_key_bytes, "big"), ec.SECP256R1(), default_backend())

    # Create public key from bytes
    public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), public_key_bytes)

    # Perform ECDH key exchange to calculate shared secret
    return private_key.exchange(ec.ECDH(), public_key)


def decrypt_aes_gcm(key, encrypted_data_and_iv, additional_data=None) -> bytes:

    # IV is appended to encrypted data
    iv = encrypted_data_and_iv[:12]
    ciphertext = encrypted_data_and_iv[12:]

    # Perform AES-GCM
    aes_gcm = AESGCM(key)
    decrypted_data = aes_gcm.decrypt(iv, ciphertext, additional_data)

    # Return result
    return decrypted_data


def decrypt_recovery_key(lskf_hash, encrypted_recovery_key):

    # The recovery key is encrypted using the hash of the LSKF
    return decrypt_aes_gcm_with_derived_key(unhexlify(encrypted_recovery_key), lskf_hash,
                                            ascii_to_bytes("V1 locally_encrypted_recovery_key"))


def decrypt_application_key(recovery_key, encrypted_application_key):

    # The application key is encrypted using the recovery key
    return decrypt_aes_gcm_with_derived_key(unhexlify(encrypted_application_key), recovery_key,
                                            ascii_to_bytes("V1 encrypted_application_key"))


def decrypt_security_domain_key(application_key, encrypted_security_domain_key):

    # The security domain key is encrypted using the application key
    return decrypt_aes_gcm(application_key, unhexlify(encrypted_security_domain_key))


def decrypt_shared_key(security_domain_key, encrypted_shared_key):

    # The shared key / domain key is encrypted using the security domain key
    return decrypt_aes_gcm_with_derived_key(unhexlify(encrypted_shared_key), security_domain_key,
                                            ascii_to_bytes("V1 shared_key"), True)


if __name__ == '__main__':

    # Load sample data
    pin = sample_pin
    pin_salt = sample_pin_salt
    encrypted_recovery_key = sample_encrypted_recovery_key
    encrypted_application_key = sample_encrypted_application_key
    encrypted_security_domain_key = sample_encrypted_security_domain_key
    encrypted_shared_key = sample_encrypted_shared_key

    # Calculate keys
    lskf_hash = get_lskf_hash(pin, pin_salt)
    recovery_key = decrypt_recovery_key(lskf_hash, encrypted_recovery_key)
    application_key = decrypt_application_key(recovery_key, encrypted_application_key)
    security_domain_key = decrypt_security_domain_key(application_key, encrypted_security_domain_key)
    shared_key = decrypt_shared_key(security_domain_key, encrypted_shared_key)

    # Print results
    print("Recovery Key:")
    print(recovery_key.hex())

    print("Application Key:")
    print(application_key.hex())

    print("Security Domain Key:")
    print(security_domain_key.hex())

    print("Shared Key:")
    print(shared_key.hex())