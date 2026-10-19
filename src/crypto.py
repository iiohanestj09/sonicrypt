"""
Modul kriptografi untuk Sonicrypt.
Menggunakan AES-256-GCM (Authenticated Encryption) dari library cryptography.

Format output encrypt():
    [ nonce (12 byte) ][ ciphertext (n byte) ][ tag (16 byte) ]
    └─────────────────────────────────────────────────────────┘
    dikembalikan oleh AESGCM.encrypt() sebagai satu kesatuan

Kontrak:
    encrypt(plaintext, passphrase) -> bytes  (nonce || ct || tag)
    decrypt(blob, passphrase)      -> bytes  (plaintext)
    decrypt dengan passphrase salah -> raise InvalidTag
"""
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12   # 96-bit, standar untuk AES-GCM
TAG_SIZE = 16     # 128-bit authentication tag


def derive_key(passphrase: str) -> bytes:
    """
    Turunkan key 256-bit dari passphrase menggunakan SHA-256.

    Catatan: cara ini sederhana, cukup untuk tugas kuliah.
    Untuk produksi gunakan KDF yang benar (PBKDF2, scrypt, Argon2)
    dengan salt, karena SHA-256 murni rentan terhadap rainbow table.
    """
    if not isinstance(passphrase, str):
        raise TypeError("passphrase harus string")
    if len(passphrase) == 0:
        raise ValueError("passphrase tidak boleh kosong")
    return hashlib.sha256(passphrase.encode("utf-8")).digest()


def encrypt(plaintext: bytes, passphrase: str) -> bytes:
    """
    Enkripsi plaintext dengan AES-256-GCM.

    Return: nonce (12 byte) || ciphertext || tag (16 byte).
    Nonce dibuat acak setiap pemanggilan, jadi encrypt() dua kali
    dengan input sama akan menghasilkan output berbeda.
    """
    if not isinstance(plaintext, (bytes, bytearray)):
        raise TypeError("plaintext harus bytes")
    key = derive_key(passphrase)
    nonce = os.urandom(NONCE_SIZE)
    aes = AESGCM(key)
    ct_and_tag = aes.encrypt(nonce, bytes(plaintext), None)
    return nonce + ct_and_tag


def decrypt(blob: bytes, passphrase: str) -> bytes:
    """
    Dekripsi blob hasil encrypt().

    Raise InvalidTag jika:
    - passphrase salah
    - data di-tamper (audio terkompresi, resample, dsb)
    """
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