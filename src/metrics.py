import hashlib

import numpy as np


def mse(orig: np.ndarray, stego: np.ndarray) -> float:
    if orig.shape != stego.shape:
        raise ValueError(
            f"shape beda: orig {orig.shape} vs stego {stego.shape}"
        )
    a = orig.astype(np.float64)
    b = stego.astype(np.float64)
    return float(np.mean((a - b) ** 2))


def snr_db(orig: np.ndarray, stego: np.ndarray) -> float:
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
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data harus bytes")
    return hashlib.sha256(bytes(data)).hexdigest()


def capacity_bytes(samples: np.ndarray) -> int:
    return int(samples.size // 8)