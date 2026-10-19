import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from src.stego import read_wav, write_wav

INPUT_WAV = (
    Path(__file__).resolve().parent.parent / "input" / "Married_Life.wav"
)


#^ S1 — Baca WAV valid
# Verifikasi: params sesuai spesifikasi file, samples int16 1D dengan
# panjang = nframes * nchannels.
def test_read_valid_wav():
    if not INPUT_WAV.exists():
        pytest.skip(f"file input tidak ditemukan: {INPUT_WAV}")
    samples, params = read_wav(INPUT_WAV)
    assert params["nchannels"] == 2
    assert params["sampwidth"] == 2
    assert params["framerate"] == 48000
    assert params["comptype"] == "NONE"
    assert samples.dtype == np.int16
    assert samples.ndim == 1
    assert samples.size == params["nframes"] * params["nchannels"]


#^ S2 — Round-trip write/read lossless
# Verifikasi: sample yang ditulis lalu dibaca ulang identik byte-per-byte,
# dan params juga identik. Tidak bergantung pada file input eksternal.
def test_write_read_roundtrip(tmp_path):
    rng = np.random.default_rng(seed=42)
    samples = rng.integers(-30000, 30000, size=2000, dtype=np.int16)
    params = {
        "nchannels": 1,
        "sampwidth": 2,
        "framerate": 44100,
        "nframes": 2000,
        "comptype": "NONE",
        "compname": "not compressed",
    }
    out = tmp_path / "roundtrip.wav"
    write_wav(out, samples, params)
    samples2, params2 = read_wav(out)
    assert params2 == params
    assert np.array_equal(samples, samples2)


#^ S3 — File tidak ada
# Verifikasi: read_wav raise FileNotFoundError sebelum mencoba membuka.
def test_read_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_wav(tmp_path / "tidak_ada.wav")


#^ S4 — Format bukan PCM 16-bit
# Verifikasi: WAV 8-bit (sampwidth=1) ditolak dengan ValueError.
def test_read_non_16bit_rejected(tmp_path):
    path = tmp_path / "8bit.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(44100)
        w.writeframes(b"\x80" * 200)
    with pytest.raises(ValueError):
        read_wav(path)


#^ S5 — Write samples bukan numpy / dtype salah
# Verifikasi: write_wav raise TypeError untuk list dan untuk array non-int16.
def test_write_invalid_samples(tmp_path):
    params = {
        "nchannels": 1,
        "sampwidth": 2,
        "framerate": 44100,
        "nframes": 100,
        "comptype": "NONE",
        "compname": "not compressed",
    }
    with pytest.raises(TypeError):
        write_wav(tmp_path / "a.wav", [0] * 100, params)
    with pytest.raises(TypeError):
        write_wav(tmp_path / "b.wav", np.zeros(100, dtype=np.int32), params)


#^ S6 — Write ukuran sample tidak konsisten
# Verifikasi: write_wav raise ValueError jika samples.size tidak habis
# dibagi nchannels (stereo butuh jumlah sample genap).
def test_write_size_mismatch(tmp_path):
    params = {
        "nchannels": 2,
        "sampwidth": 2,
        "framerate": 44100,
        "nframes": 50,
        "comptype": "NONE",
        "compname": "not compressed",
    }
    with pytest.raises(ValueError):
        write_wav(tmp_path / "c.wav", np.zeros(101, dtype=np.int16), params)
        
        
#^ S7 — bytes_to_bits urutan MSB-first
# Verifikasi: 0x00 semua 0, 0xFF semua 1, 0x80 bit pertama 1 sisanya 0,
# 0x01 bit terakhir 1 sisanya 0.
def test_bytes_to_bits_msb_first():
    from src.stego import bytes_to_bits

    assert bytes_to_bits(b"\x00").tolist() == [0] * 8
    assert bytes_to_bits(b"\xff").tolist() == [1] * 8
    assert bytes_to_bits(b"\x80").tolist() == [1, 0, 0, 0, 0, 0, 0, 0]
    assert bytes_to_bits(b"\x01").tolist() == [0, 0, 0, 0, 0, 0, 0, 1]
    assert bytes_to_bits(b"").size == 0


#^ S8 — Round-trip bytes -> bits -> bytes
# Verifikasi: hasil konversi bolak-balik identik dengan input untuk
# berbagai ukuran, termasuk 1 MB dan data acak.
def test_bytes_bits_roundtrip():
    from src.stego import bytes_to_bits, bits_to_bytes

    for size in [0, 1, 16, 1024, 1024 * 1024]:
        data = bytes((i * 31 + 7) & 0xFF for i in range(size))
        assert bits_to_bytes(bytes_to_bits(data)) == data


#^ S9 — bits_to_bytes tolak panjang bukan kelipatan 8
# Verifikasi: array bit dengan panjang 1, 7, 9, dst -> ValueError.
def test_bits_to_bytes_bad_length():
    from src.stego import bits_to_bytes

    with pytest.raises(ValueError):
        bits_to_bytes(np.array([1, 0, 1], dtype=np.uint8))
    with pytest.raises(ValueError):
        bits_to_bytes(np.zeros(7, dtype=np.uint8))
    with pytest.raises(ValueError):
        bits_to_bytes(np.zeros(9, dtype=np.uint8))


#^ S10 — bits_to_bytes tolak nilai bukan 0/1
# Verifikasi: array dengan nilai 2, 255, atau -1 -> ValueError.
def test_bits_to_bytes_bad_values():
    from src.stego import bits_to_bytes

    with pytest.raises(ValueError):
        bits_to_bytes(np.array([0, 0, 2, 0, 0, 0, 0, 0], dtype=np.uint8))
    with pytest.raises(ValueError):
        bits_to_bytes(np.array([0, 0, 0, 0, 0, 0, 0, 255], dtype=np.uint8))
    with pytest.raises(ValueError):
        bits_to_bytes(np.array([0, 0, 0, 0, 0, 0, 0, -1], dtype=np.int8))


#^ S11 — bytes_to_bits tolak input bukan bytes
# Verifikasi: string, list, int -> TypeError.
def test_bytes_to_bits_bad_input():
    from src.stego import bytes_to_bits

    with pytest.raises(TypeError):
        bytes_to_bits("bukan bytes")
    with pytest.raises(TypeError):
        bytes_to_bits([0, 1, 2])
    with pytest.raises(TypeError):
        bytes_to_bits(123)
        
        
def _make_test_audio(n_samples=8000, seed=42):
    """Random int16 di rentang [-10000, 10000] untuk test audio."""
    rng = np.random.default_rng(seed)
    return rng.integers(-10000, 10000, size=n_samples, dtype=np.int16)


#^ S12 — Embed lalu extract round-trip
# Verifikasi: payload yang disisipkan dapat diekstrak kembali identik.
def test_embed_extract_roundtrip():
    from src.stego import embed_lsb, extract_lsb

    samples = _make_test_audio(8000)
    payload = b"PESAN RAHASIA"
    stego = embed_lsb(samples, payload)
    assert extract_lsb(stego, len(payload)) == payload


#^ S13 — Embed tolak payload > kapasitas
# Verifikasi: 100 sample = 12.5 byte kapasitas, payload 13 byte harus ditolak.
def test_embed_capacity_exceeded():
    from src.stego import embed_lsb

    samples = _make_test_audio(100)
    with pytest.raises(ValueError):
        embed_lsb(samples, b"x" * 13)


#^ S14 — Extract tolak nbytes > kapasitas
# Verifikasi: minta baca 13 byte dari 100 sample -> ValueError.
def test_extract_capacity_exceeded():
    from src.stego import extract_lsb

    samples = _make_test_audio(100)
    with pytest.raises(ValueError):
        extract_lsb(samples, 13)


#^ S15 — Embed tidak modify input
# Verifikasi: samples asli identik sebelum dan sesudah embed.
def test_embed_does_not_modify_input():
    from src.stego import embed_lsb

    samples = _make_test_audio(1000)
    original = samples.copy()
    embed_lsb(samples, b"test")
    assert np.array_equal(samples, original), "input tidak boleh berubah"


#^ S16 — Berbagai ukuran payload
# Verifikasi: payload 0 B, 1 B, 16 B, 1 KB, 8000 B round-trip berhasil.
def test_embed_extract_various_sizes():
    from src.stego import embed_lsb, extract_lsb

    samples = _make_test_audio(80000)  # 10000 byte kapasitas
    for size in [0, 1, 16, 1024, 8000]:
        payload = bytes((i * 31 + 7) & 0xFF for i in range(size))
        stego = embed_lsb(samples, payload)
        assert extract_lsb(stego, size) == payload, f"gagal size={size}"


#^ S17 — SNR tetap tinggi setelah embed
# Verifikasi: perubahan LSB tidak merusak kualitas audio (SNR > 60 dB).
def test_embed_snr_high():
    from src.metrics import snr_db
    from src.stego import embed_lsb

    samples = _make_test_audio(80000)
    stego = embed_lsb(samples, b"x" * 1000)  # 8000 sample LSB berubah
    snr = snr_db(samples, stego)
    assert snr > 60.0, f"SNR terlalu rendah: {snr:.2f} dB"


#^ S18 — LSB yang tertanam benar-benar payload
# Verifikasi: bit LSB sample[0..15] persis sama dengan bit payload,
# dan sample[16:] tidak berubah sama sekali.
def test_embed_lsb_correct():
    from src.stego import bytes_to_bits, embed_lsb

    samples = _make_test_audio(1000)
    payload = b"AB"  # 16 bit
    stego = embed_lsb(samples, payload)

    bits_expected = bytes_to_bits(payload)
    for i, expected_bit in enumerate(bits_expected):
        assert (int(stego[i]) & 1) == expected_bit, f"bit ke-{i} salah"
    # Sample setelah bit terakhir tidak boleh berubah
    assert np.array_equal(samples[16:], stego[16:])


#^ S19 — Extract nbytes negatif
# Verifikasi: nbytes < 0 -> ValueError.
def test_extract_negative_nbytes():
    from src.stego import extract_lsb

    samples = _make_test_audio(100)
    with pytest.raises(ValueError):
        extract_lsb(samples, -1)


#^ S20 — Extract nbytes = 0
# Verifikasi: nbytes 0 -> bytes kosong, tanpa error.
def test_extract_zero_bytes():
    from src.stego import extract_lsb

    samples = _make_test_audio(100)
    assert extract_lsb(samples, 0) == b""