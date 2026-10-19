import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12   # 96-bit, standar untuk AES-GCM
TAG_SIZE = 16     # 128-bit authentication tag


def derive_key(passphrase: str) -> bytes:
    if not isinstance(passphrase, str):
        raise TypeError("passphrase harus string")
    if len(passphrase) == 0:
        raise ValueError("passphrase tidak boleh kosong")
    return hashlib.sha256(passphrase.encode("utf-8")).digest()


def encrypt(plaintext: bytes, passphrase: str) -> bytes:
    if not isinstance(plaintext, (bytes, bytearray)):
        raise TypeError("plaintext harus bytes")
    key = derive_key(passphrase)
    nonce = os.urandom(NONCE_SIZE)
    aes = AESGCM(key)
    ct_and_tag = aes.encrypt(nonce, bytes(plaintext), None)
    return nonce + ct_and_tag


def decrypt(blob: bytes, passphrase: str) -> bytes:
    if not isinstance(blob, (bytes, bytearray)):
        raise TypeError("blob harus bytes")
    if len(blob) < NONCE_SIZE + TAG_SIZE:
        raise ValueError(
            f"blob terlalu pendek (min {NONCE_SIZE + TAG_SIZE} byte, "
            f"dapat {len(blob)})"
        )
    nonce = bytes(blob[:NONCE_SIZE])
    ct_and_tag = bytes(blob[NONCE_SIZE:])
    key = derive_key(passphrase)
    return AESGCM(key).decrypt(nonce, ct_and_tag, None)