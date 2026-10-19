"""
Test untuk src/pipeline.py — gabungan crypto + stego dengan header.

Jalankan: pytest tests/pipeline_test.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest
from cryptography.exceptions import InvalidTag

from src.pipeline import embed, extract, MAGIC, HEADER_SIZE
from src.stego import wav_bytes


def _make_audio_wav(n_samples=8000, seed=42) -> bytes:
    """Generate WAV bytes in-memory dari random samples."""
    rng = np.random.default_rng(seed)
    samples = rng.integers(-10000, 10000, size=n_samples, dtype=np.int16)
    params = {
        "nchannels": 1,
        "sampwidth": 2,
        "framerate": 44100,
        "nframes": n_samples,
        "comptype": "NONE",
        "compname": "not compressed",
    }
    return wav_bytes(samples, params)


#^ P1 — Round-trip embed/extract in-memory
# Verifikasi: plaintext utuh setelah embed lalu extract, dengan audio
# input berupa bytes (bukan path).
def test_roundtrip_in_memory():
    audio = _make_audio_wav(8000)
    plaintext = b"PESAN RAHASIA"
    stego_bytes, info_embed = embed(audio, plaintext, "abc")
    recovered, info_extract = extract(stego_bytes, "abc")
    assert recovered == plaintext
    assert info_embed["plaintext_bytes"] == len(plaintext)
    assert info_extract["plaintext_bytes"] == len(plaintext)


#^ P2 — Passphrase salah
# Verifikasi: extract dengan passphrase keliru raise InvalidTag
# (diteruskan dari crypto.decrypt).
def test_wrong_passphrase():
    audio = _make_audio_wav(8000)
    stego_bytes, _ = embed(audio, b"rahasia", "benar")
    with pytest.raises(InvalidTag):
        extract(stego_bytes, "salah")


#^ P3 — Audio bukan stego (MAGIC tidak cocok)
# Verifikasi: extract pada audio random tanpa embed raise ValueError
# dengan pesan yang menyebut MAGIC.
def test_wrong_magic():
    audio = _make_audio_wav(8000)
    with pytest.raises(ValueError, match="MAGIC"):
        extract(audio, "abc")


#^ P4 — Berbagai ukuran plaintext
# Verifikasi: plaintext 1 B, 16 B, 1 KB, 5 KB semuanya round-trip.
def test_various_sizes():
    audio = _make_audio_wav(80000)
    for size in [1, 16, 1024, 5000]:
        plaintext = bytes((i * 31 + 7) & 0xFF for i in range(size))
        stego_bytes, _ = embed(audio, plaintext, "abc")
        recovered, _ = extract(stego_bytes, "abc")
        assert recovered == plaintext, f"gagal size={size}"


#^ P5 — Kapasitas kurang saat embed
# Verifikasi: plaintext melebihi kapasitas audio -> ValueError.
def test_capacity_exceeded():
    audio = _make_audio_wav(100)  # 12 byte kapasitas, header saja 10
    with pytest.raises(ValueError, match="kapasitas"):
        embed(audio, b"x" * 20, "abc")


#^ P6 — Output ke file path
# Verifikasi: embed dengan output_path benar-benar menulis file WAV,
# dan file itu bisa di-extract kembali.
def test_embed_to_file(tmp_path):
    audio = _make_audio_wav(8000)
    out = tmp_path / "stego.wav"
    plaintext = b"hello file"
    embed(audio, plaintext, "abc", output_path=out)
    assert out.exists()
    recovered, _ = extract(out, "abc")
    assert recovered == plaintext


#^ P7 — File WAV asli 48 MB
# Verifikasi: embed + extract pada married_life.wav sungguhan,
# sekaligus cek SNR tetap tinggi. Skip kalau file tidak ada.
def test_married_life_file():
    input_path = (
        Path(__file__).resolve().parent.parent
        / "data" / "input" / "married_life.wav"
    )
    if not input_path.exists():
        pytest.skip(f"file tidak ditemukan: {input_path}")
    plaintext = b"test dengan audio asli"
    stego_bytes, info = embed(input_path, plaintext, "abc")
    recovered, _ = extract(stego_bytes, "abc")
    assert recovered == plaintext
    assert info["snr_db"] > 60.0, f"SNR terlalu rendah: {info['snr_db']:.2f} dB"