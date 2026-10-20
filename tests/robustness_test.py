import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest
from cryptography.exceptions import InvalidTag

from src.pipeline import embed, extract
from src.robustness import run_robustness, _attack_noise, _attack_resample, _attack_crop
from src.stego import wav_bytes, read_wav_bytes


def _make_audio_wav(n_samples=100_000) -> bytes:
    rng = np.random.default_rng(42)
    samples = rng.integers(-10000, 10000, size=n_samples, dtype=np.int16)
    params = {
        "nchannels": 1, "sampwidth": 2, "framerate": 48000,
        "nframes": n_samples, "comptype": "NONE", "compname": "not compressed",
    }
    return wav_bytes(samples, params)


#^ R1 — Baseline (tanpa attack) harus sukses
# Verifikasi: sistem bisa ekstrak pesan dari stego asli.
def test_baseline_success():
    audio = _make_audio_wav()
    stego_bytes, _ = embed(audio, b"rahasia", "abc")
    df = run_robustness(stego_bytes, "abc")
    baseline = df[df["attack"] == "None (baseline)"].iloc[0]
    assert baseline["status"] == "SUKSES (Bocor!)"


#^ R2 — Semua attack harus menggagalkan ekstraksi
# Verifikasi: No attack bisa mengekstrak pesan (menunjukkan LSB rapuh).
def test_all_attacks_fail():
    audio = _make_audio_wav()
    stego_bytes, _ = embed(audio, b"rahasia", "abc")
    df = run_robustness(stego_bytes, "abc")
    
    attacks = df[df["attack"] != "None (baseline)"]
    for _, row in attacks.iterrows():
        assert "GAGAL" in row["status"], f"Attack {row['attack']} malah berhasil!"
        assert row["plaintext_len"] == 0


#^ R3 — Noise menghancurkan LSB
# Verifikasi: noise membuat extract gagal, baik karena MAGIC hancur
# (ValueError) atau karena ciphertext rusak (InvalidTag). Dua-duanya
# membuktikan sistem menolak data yang dimodifikasi.
def test_noise_destroys_lsb():
    audio = _make_audio_wav()
    stego_bytes, _ = embed(audio, b"rahasia", "abc")
    samples, params = read_wav_bytes(stego_bytes)

    noisy = _attack_noise(samples, snr_db=20.0)
    noisy_wav = wav_bytes(noisy, params)

    with pytest.raises((InvalidTag, ValueError)):
        extract(noisy_wav, "abc")


#^ R4 — Crop menghapus header
# Verifikasi: memotong 1 detik pertama menghilangkan MAGIC,
# menghasilkan ValueError.
def test_crop_destroys_header():
    audio = _make_audio_wav()
    stego_bytes, _ = embed(audio, b"rahasia", "abc")
    samples, params = read_wav_bytes(stego_bytes)
    
    cropped, crop_params = _attack_crop(samples, params, crop_sec=0.5)
    cropped_wav = wav_bytes(cropped, crop_params)
    
    with pytest.raises(ValueError):
        extract(cropped_wav, "abc")
        

#^ R5 — Modifikasi 1 bit ciphertext memicu InvalidTag
# Verifikasi: ubah 1 bit di area ciphertext (setelah header) untuk
# memastikan AES-GCM menolak, bukan validasi MAGIC.
def test_single_bit_tamper_ciphertext():
    audio = _make_audio_wav()
    stego_bytes, _ = embed(audio, b"rahasia", "abc")
    samples, params = read_wav_bytes(stego_bytes)

    # Header 10 byte = 80 sample. Ubah LSB sample ke-100 (di area ciphertext).
    tampered = samples.copy()
    tampered[100] = tampered[100] ^ 1
    tampered_wav = wav_bytes(tampered, params)

    with pytest.raises(InvalidTag):
        extract(tampered_wav, "abc")
        
#^ R6 — Single-bit flip di ciphertext memicu InvalidTag
# Verifikasi: ubah 1 sample di area ciphertext (bukan header). MAGIC
# harus lolos, tapi AES-GCM menolak karena tag tidak cocok.
def test_single_bit_flip_ciphertext():
    from src.pipeline import HEADER_SIZE
    audio = _make_audio_wav()
    stego_bytes, _ = embed(audio, b"rahasia", "abc")
    samples, params = read_wav_bytes(stego_bytes)

    target = HEADER_SIZE * 8 + 20  # = 100, di area ciphertext
    tampered = samples.copy()
    tampered[target] = tampered[target] ^ 1
    tampered_wav = wav_bytes(tampered, params)

    with pytest.raises(InvalidTag):
        extract(tampered_wav, "abc")


#^ R7 — Noise di ciphertext (header utuh) memicu InvalidTag
# Verifikasi: noise SNR 40 dB hanya di area ciphertext. MAGIC harus
# tetap utuh, tapi ciphertext rusak -> InvalidTag.
def test_ciphertext_noise_triggers_invalid_tag():
    from src.robustness import _attack_ciphertext_noise
    audio = _make_audio_wav()
    stego_bytes, _ = embed(audio, b"rahasia panjang untuk uji noise ciphertext", "abc")
    samples, params = read_wav_bytes(stego_bytes)

    tampered = _attack_ciphertext_noise(samples, params, snr_db=40.0, seed=42)
    tampered_wav = wav_bytes(tampered, params)

    with pytest.raises(InvalidTag):
        extract(tampered_wav, "abc")