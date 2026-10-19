import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from src.metrics import mse, snr_db, ber, sha256, capacity_bytes


#^ M1 — MSE dasar
# Verifikasi: mse(a,a) = 0.0 dan mse dengan 1 sample beda 1 = 1/n.
def test_mse_basic():
    a = np.array([100, 200, 300], dtype=np.int16)
    b = np.array([100, 200, 301], dtype=np.int16)
    assert mse(a, a) == 0.0
    assert abs(mse(a, b) - 1 / 3) < 1e-9


#^ M2 — SNR
# Verifikasi: inf untuk identik, -inf untuk sinyal nol, nilai positif kecil untuk noise 1 sample.
def test_snr_db():
    a = np.array([100, 200, 300], dtype=np.int16)
    b = np.array([100, 200, 301], dtype=np.int16)
    assert snr_db(a, a) == float("inf")
    assert snr_db(np.zeros(10, dtype=np.int16), np.ones(10, dtype=np.int16)) == float("-inf")
    # signal = 100²+200²+300² = 140000, noise = 1 → SNR ≈ 51.46 dB
    snr = snr_db(a, b)
    assert 51.0 < snr < 52.0, f"SNR di luar rentang: {snr}"


#^ M3 — BER
# Verifikasi: 0.0 untuk identik, 0.4 untuk 2 bit beda dari 5, 0.0 untuk array kosong.
def test_ber():
    assert ber(np.array([1, 0, 1, 0, 1]), np.array([1, 0, 1, 0, 1])) == 0.0
    assert ber(np.array([1, 0, 1, 0, 1]), np.array([1, 1, 1, 0, 0])) == 0.4
    assert ber(np.array([], dtype=np.uint8), np.array([], dtype=np.uint8)) == 0.0


#^ M4 — SHA-256
# Verifikasi: hash empty string sesuai referensi NIST, konsisten, dan beda untuk input beda.
def test_sha256():
    assert sha256(b"") == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert sha256(b"halo dunia") == sha256(b"halo dunia")
    assert sha256(b"a") != sha256(b"b")
    assert len(sha256(b"x")) == 64


#^ M5 — Kapasitas byte
# Verifikasi: floor(n_samples / 8), termasuk kasus tidak habis dibagi 8.
def test_capacity_bytes():
    assert capacity_bytes(np.zeros(8000, dtype=np.int16)) == 1000
    assert capacity_bytes(np.zeros(8007, dtype=np.int16)) == 1000
    assert capacity_bytes(np.zeros(7, dtype=np.int16)) == 0
    assert capacity_bytes(np.zeros(0, dtype=np.int16)) == 0


#^ M6 — Input invalid
# Verifikasi: shape mismatch, panjang beda, dan tipe salah raise exception jelas.
def test_invalid_input():
    cases = [
        (ValueError, lambda: mse(np.zeros(10), np.zeros(20))),
        (ValueError, lambda: snr_db(np.zeros(10), np.zeros(20))),
        (ValueError, lambda: ber(np.zeros(10), np.zeros(20))),
        (TypeError,  lambda: sha256("bukan bytes")),
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