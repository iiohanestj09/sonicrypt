import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cryptography.exceptions import InvalidTag

from src.crypto import encrypt, decrypt


#^ C1 — Round-trip
# Verifikasi: encrypt() lalu decrypt() mengembalikan plaintext utuh.
# Panjang blob harus = plaintext + 28 byte (12 nonce + 16 tag).
def test_roundtrip():
    blob = encrypt(b"halo dunia", "abc")
    assert len(blob) == 10 + 12 + 16, "panjang blob harus plaintext + 28"
    assert decrypt(blob, "abc") == b"halo dunia"


#^ C2 — Nonce random
# Verifikasi: dua encrypt() dengan input identik menghasilkan output
# berbeda. Nonce dibuat acak setiap panggilan (os.urandom(12)).
def test_nonce_random():
    assert encrypt(b"x", "abc") != encrypt(b"x", "abc")


#^ C3 — Passphrase salah
# Verifikasi: decrypt() dengan passphrase keliru raise InvalidTag,
# bukan mengembalikan bytes acak. Bukti authenticated encryption.
def test_wrong_passphrase():
    blob = encrypt(b"x", "abc")
    try:
        decrypt(blob, "salah")
    except InvalidTag:
        return
    raise AssertionError("harusnya raise InvalidTag")


#^ C4 — Berbagai ukuran plaintext
# Verifikasi: untuk ukuran 0 B sampai 1 MB, panjang blob selalu
# = plaintext + 28 byte, dan round-trip selalu berhasil.
def test_various_sizes():
    for size in [0, 1, 16, 1024, 1024 * 1024]:
        plaintext = b"x" * size
        blob = encrypt(plaintext, "abc")
        assert decrypt(blob, "abc") == plaintext, f"gagal size={size}"
        assert len(blob) == size + 28, f"panjang salah size={size}"


#^ C5 — Data tampered
# Verifikasi: 1 byte ciphertext yang diubah membuat decrypt() raise
# InvalidTag. Simulasi skenario audio yang kena kompresi/resample.
def test_tampered():
    blob = encrypt(b"pesan penting", "abc")
    rusak = blob[:-1] + bytes([blob[-1] ^ 0xFF])
    try:
        decrypt(rusak, "abc")
    except InvalidTag:
        return
    raise AssertionError("harusnya raise InvalidTag")


#^ C6 — Input invalid
# Verifikasi: validasi input di crypto.py bekerja.
#   - plaintext bukan bytes      -> TypeError
#   - passphrase kosong          -> ValueError
#   - blob terlalu pendek        -> ValueError
def test_invalid_input():
    cases = [
        (TypeError,  lambda: encrypt("bukan bytes", "abc")),
        (ValueError, lambda: encrypt(b"x", "")),
        (ValueError, lambda: decrypt(b"pendek", "abc")),
    ]
    for expected_exc, fn in cases:
        try:
            fn()
        except expected_exc:
            continue
        except Exception as e:
            raise AssertionError(
                f"harusnya {expected_exc.__name__}, dapat {type(e).__name__}"
            )
        raise AssertionError(f"harusnya raise {expected_exc.__name__}")