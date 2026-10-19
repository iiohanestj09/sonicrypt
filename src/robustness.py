"""
Robustness test untuk Sonicrypt.

Menguji apakah pesan masih bisa diekstrak setelah audio stego
mengalami modifikasi umum:
  1. Add noise   : penambahan noise Gaussian (misal transmisi radio)
  2. Resample    : ubah sample rate 48kHz -> 44.1kHz (misal kualitas CD)
  3. Crop        : potong 1 detik pertama (misal edit sembarangan)
  4. Scale       : ubah volume (misal gain +20% / -20%)

Karena LSB rentan, hasil yang diharapkan adalah SEMUA attack
menggagalkan ekstraksi (InvalidTag / ValueError). Ini membuktikan
sistem mendeteksi manipulasi (authenticated encryption).

Jalankan: python -m src.robustness
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from cryptography.exceptions import InvalidTag
from scipy import signal

from src.pipeline import embed, extract
from src.stego import read_wav_bytes, wav_bytes


def _attack_noise(samples: np.ndarray, snr_db: float = 30.0) -> np.ndarray:
    """Tambah white Gaussian noise pada level SNR tertentu."""
    power_signal = np.mean(samples.astype(np.float64) ** 2)
    power_noise = power_signal / (10 ** (snr_db / 10.0))
    noise = np.random.normal(0, np.sqrt(power_noise), samples.shape)
    noisy = samples.astype(np.float64) + noise
    return np.clip(noisy, -32768, 32767).astype(np.int16)


def _attack_resample(samples: np.ndarray, params: dict, target_sr: int = 44100) -> tuple[np.ndarray, dict]:
    """Resample audio ke target_sr (misal 48k -> 44.1k)."""
    nch = params["nchannels"]
    orig_sr = params["framerate"]
    nframes = params["nframes"]

    # Reshape ke (nframes, nchannels) agar resampling tidak
    # mencampur channel kiri dan kanan
    arr = samples.reshape((nframes, nch)).astype(np.float64)
    new_frames = int(nframes * (target_sr / orig_sr))
    
    # scipy resample menggunakan FFT (cepat dan akurat)
    resampled = signal.resample(arr, new_frames, axis=0)
    
    new_samples = np.clip(resampled, -32768, 32767).astype(np.int16).flatten()
    new_params = params.copy()
    new_params["framerate"] = target_sr
    new_params["nframes"] = new_frames
    return new_samples, new_params


def _attack_crop(samples: np.ndarray, params: dict, crop_sec: float = 1.0) -> tuple[np.ndarray, dict]:
    """Potong beberapa detik pertama audio."""
    nch = params["nchannels"]
    sr = params["framerate"]
    nframes = params["nframes"]
    
    samples_to_crop = int(sr * crop_sec) * nch
    if samples_to_crop >= len(samples):
        raise ValueError("audio terlalu pendek untuk di-crop")
        
    new_samples = samples[samples_to_crop:]
    new_params = params.copy()
    new_params["nframes"] = nframes - int(sr * crop_sec)
    return new_samples, new_params


def _attack_volume(samples: np.ndarray, factor: float = 0.8) -> np.ndarray:
    """Ubah volume audio (gain)."""
    scaled = samples.astype(np.float64) * factor
    return np.clip(scaled, -32768, 32767).astype(np.int16)


def run_robustness(stego_bytes: bytes, passphrase: str) -> pd.DataFrame:
    """Jalankan semua attack, catat hasil ekstraksi."""
    samples, params = read_wav_bytes(stego_bytes)

    attacks = {
        "None (baseline)": lambda: (samples, params),
        "Add Noise (30 dB)": lambda: (_attack_noise(samples, 30.0), params),
        "Resample (48k -> 44.1k)": lambda: _attack_resample(samples, params, 44100),
        "Crop (1 detik awal)": lambda: _attack_crop(samples, params, 1.0),
        "Volume (-20%)": lambda: (_attack_volume(samples, 0.8), params),
    }

    results = []
    for name, fn in attacks.items():
        try:
            modified_samples, modified_params = fn()
            modified_wav = wav_bytes(modified_samples, modified_params)
            
            # Coba ekstrak
            _, info = extract(modified_wav, passphrase)
            results.append({
                "attack": name,
                "status": "SUKSES (Bocor!)",
                "error": "-",
                "plaintext_len": info["plaintext_bytes"]
            })
        except (InvalidTag, ValueError) as e:
            err_msg = "InvalidTag (tampered)" if isinstance(e, InvalidTag) else str(e)
            # Ringkas pesan error yang panjang
            if len(err_msg) > 60: err_msg = err_msg[:57] + "..."
            results.append({
                "attack": name,
                "status": "GAGAL (Aman)",
                "error": err_msg,
                "plaintext_len": 0
            })
        except Exception as e:
            results.append({
                "attack": name,
                "status": "GAGAL (Error lain)",
                "error": type(e).__name__,
                "plaintext_len": 0
            })

    return pd.DataFrame(results)


def main() -> int:
    input_path = Path("input/married_life.wav")
    if not input_path.exists():
        print(f"ERROR: {input_path} tidak ditemukan.")
        return 1

    print("Menyiapkan stego audio untuk diuji...")
    plaintext = b"Ini pesan rahasia untuk diuji ketahanannya."
    passphrase = "robustness"
    stego_bytes, _ = embed(input_path, plaintext, passphrase)

    print("Menjalankan attack...")
    df = run_robustness(stego_bytes, passphrase)
    
    print("\n" + "="*70)
    print("HASIL ROBUSTNESS TEST")
    print("="*70)
    print(df.to_string(index=False))
    print("="*70)
    print("Catatan: 'GAGAL (Aman)' berarti sistem berhasil mendeteksi")
    print("manipulasi dan menolak memberikan data yang sudah rusak.")
    
    # Simpan ke CSV
    out_path = Path("output/robustness_results.csv")
    out_path.parent.mkdir(exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\nCSV tersimpan: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())