"""
Quality metrics for Sonicrypt.

Semua fungsi menerima numpy array int16 (samples audio) atau bytes/bits,
dan mengembalikan float. Tidak ada I/O file di sini — biar bisa dipakai
di pipeline.py, benchmark.py, dan app.py sekaligus.
"""
import hashlib

import numpy as np


def mse(orig: np.ndarray, stego: np.ndarray) -> float:
    """
    Mean Squared Error antara dua array sample audio.

    Cast ke float64 dulu supaya tidak overflow saat pengurangan
    (int16 selisih 100 - 200 = -100, tapi 100 - (-100) bisa overflow
    kalau dibiarkan int16).
    """
    if orig.shape != stego.shape:
        raise ValueError(
            f"shape beda: orig {orig.shape} vs stego {stego.shape}"
        )
    a = orig.astype(np.float64)
    b = stego.astype(np.float64)
    return float(np.mean((a - b) ** 2))


def snr_db(orig: np.ndarray, stego: np.ndarray) -> float:
    """
    Signal-to-Noise Ratio dalam dB.

    SNR = 10 * log10( sum(orig^2) / sum((orig - stego)^2) )

    Return:
    - inf  jika orig == stego (tidak ada noise)
    - -inf jika orig seluruhnya nol (tidak ada sinyal)
    """
    if orig.shape != stego.shape:
        raise ValueError(
            f"shape beda: orig {orig.shape} vs stego {stego.shape}"
        )
    a = orig.astype(np.float64)
    b = stego.astype(np.float64)
    noise = a - b

    power_signal = float(np.sum(a ** 2))
    power_noise = float(np.sum(noise ** 2))

    if power_noise == 0.0:
        return float("inf")
    if power_signal == 0.0:
        return float("-inf")
    return float(10.0 * np.log10(power_signal / power_noise))


def ber(bits_a: np.ndarray, bits_b: np.ndarray) -> float:
    """
    Bit Error Rate antara dua array bit (0/1).

    Dipakai untuk bandingkan ciphertext asli vs ciphertext hasil ekstraksi.
    Jika ekstraksi sempurna, BER = 0.
    """
    a = np.asarray(bits_a).ravel()
    b = np.asarray(bits_b).ravel()
    if a.shape != b.shape:
        raise ValueError(
            f"panjang beda: {a.size} vs {b.size} bit"
        )
    if a.size == 0:
        return 0.0
    return float(np.mean(a != b))


def sha256(data: bytes) -> str:
    """Hash SHA-256 sebagai hex string. Untuk cek integritas plaintext."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data harus bytes")
    return hashlib.sha256(bytes(data)).hexdigest()


def capacity_bytes(samples: np.ndarray) -> int:
    """
    Kapasitas LSB dalam byte: setiap sample menyumbang 1 bit.

    Contoh: 1 juta sample -> 1.000.000 bit -> 125.000 byte.
    """
    return int(samples.size // 8)