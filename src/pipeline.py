"""
Pipeline Sonicrypt: gabungan crypto + stego.

Format payload yang disisipkan ke audio:

    [ MAGIC (6) ][ blob_length (4, big-endian) ][ blob (nonce + ct + tag) ]

- MAGIC       : b"SONIC1", untuk validasi bahwa audio adalah stego Sonicrypt
- blob_length : panjang blob setelah header, dalam byte
- blob        : output crypto.encrypt(), sudah termasuk nonce 12 byte
                dan tag 16 byte di dalamnya

Header total 10 byte. Kapasitas efektif payload = capacity_bytes(samples) - 10.
"""
import time
from pathlib import Path

import numpy as np

from src import crypto
from src.metrics import mse, snr_db, capacity_bytes
from src.stego import (
    read_wav,
    read_wav_bytes,
    wav_bytes,
    embed_lsb,
    extract_lsb,
)

MAGIC = b"SONIC1"
MAGIC_LEN = 6
LENGTH_LEN = 4
HEADER_SIZE = MAGIC_LEN + LENGTH_LEN  # 10


def _read_audio(audio_input):
    """Terima path atau bytes, return (samples, params)."""
    if isinstance(audio_input, (str, Path)):
        return read_wav(audio_input)
    if isinstance(audio_input, (bytes, bytearray)):
        return read_wav_bytes(bytes(audio_input))
    raise TypeError(
        f"audio_input harus path atau bytes, dapat {type(audio_input).__name__}"
    )


def embed(audio_input, plaintext, passphrase, output_path=None):
    """
    Sisipkan plaintext terenkripsi ke audio.

    Parameters
    ----------
    audio_input : str | Path | bytes
        Path ke file WAV, atau bytes WAV in-memory.
    plaintext : bytes
        Pesan yang akan disembunyikan.
    passphrase : str
        Kunci enkripsi.
    output_path : str | Path | None
        Kalau diisi, hasil stego ditulis ke file ini.

    Returns
    -------
    stego_bytes : bytes
        WAV stego dalam bentuk bytes.
    info : dict
        encrypt_time_s, embed_time_s, plaintext_bytes, blob_bytes,
        payload_bytes, capacity_bytes, mse, snr_db.
    """
    if not isinstance(plaintext, (bytes, bytearray)):
        raise TypeError(
            f"plaintext harus bytes, dapat {type(plaintext).__name__}"
        )
    if len(plaintext) == 0:
        raise ValueError("plaintext tidak boleh kosong")

    samples, params = _read_audio(audio_input)
    original = samples.copy()

    t0 = time.perf_counter()
    blob = crypto.encrypt(bytes(plaintext), passphrase)
    encrypt_time = time.perf_counter() - t0

    if len(blob) > (1 << 32) - 1:
        raise ValueError("plaintext terlalu besar (> 4 GB)")

    header = MAGIC + len(blob).to_bytes(LENGTH_LEN, "big")
    payload = header + blob

    capacity = capacity_bytes(samples)
    if len(payload) > capacity:
        raise ValueError(
            f"kapasitas kurang: butuh {len(payload)} byte, "
            f"tersedia {capacity} byte"
        )

    t0 = time.perf_counter()
    stego_samples = embed_lsb(samples, payload)
    embed_time = time.perf_counter() - t0

    stego_bytes = wav_bytes(stego_samples, params)

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(stego_bytes)

    info = {
        "encrypt_time_s": encrypt_time,
        "embed_time_s": embed_time,
        "plaintext_bytes": len(plaintext),
        "blob_bytes": len(blob),
        "payload_bytes": len(payload),
        "capacity_bytes": capacity,
        "mse": mse(original, stego_samples),
        "snr_db": snr_db(original, stego_samples),
    }
    return stego_bytes, info


def extract(audio_input, passphrase):
    """
    Ekstrak dan dekripsi plaintext dari audio stego.

    Returns
    -------
    plaintext : bytes
    info : dict
        extract_time_s, decrypt_time_s, plaintext_bytes, blob_bytes.

    Raises
    ------
    ValueError : MAGIC tidak cocok atau header tidak valid.
    InvalidTag : passphrase salah atau data rusak (dari crypto.decrypt).
    """
    samples, _ = _read_audio(audio_input)

    if samples.size < HEADER_SIZE * 8:
        raise ValueError(
            f"audio terlalu pendek untuk membaca header "
            f"(butuh minimal {HEADER_SIZE * 8} sample, "
            f"tersedia {samples.size})"
        )

    header = extract_lsb(samples, HEADER_SIZE)
    magic = header[:MAGIC_LEN]
    if magic != MAGIC:
        raise ValueError(
            f"MAGIC tidak cocok: {magic!r} != {MAGIC!r} "
            f"(audio bukan stego Sonicrypt, atau rusak)"
        )

    blob_len = int.from_bytes(header[MAGIC_LEN:HEADER_SIZE], "big")
    total_needed = HEADER_SIZE + blob_len
    if total_needed * 8 > samples.size:
        raise ValueError(
            f"blob_length di header ({blob_len} byte) melebihi "
            f"kapasitas audio"
        )

    t0 = time.perf_counter()
    blob = extract_lsb(samples, total_needed)[HEADER_SIZE:]
    extract_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    plaintext = crypto.decrypt(blob, passphrase)
    decrypt_time = time.perf_counter() - t0

    info = {
        "extract_time_s": extract_time,
        "decrypt_time_s": decrypt_time,
        "plaintext_bytes": len(plaintext),
        "blob_bytes": blob_len,
    }
    return plaintext, info