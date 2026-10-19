import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from src.validate_audio import validate_one, collect_files
from src.stego import wav_bytes


def _write_wav(path, n_samples=100_000):
    rng = np.random.default_rng(42)
    samples = rng.integers(-10000, 10000, size=n_samples, dtype=np.int16)
    params = {
        "nchannels": 1, "sampwidth": 2, "framerate": 44100,
        "nframes": n_samples, "comptype": "NONE", "compname": "not compressed",
    }
    path.write_bytes(wav_bytes(samples, params))


#^ V1 — File valid lolos
# Verifikasi: WAV PCM 16-bit sintetis lolos validasi, params dan
# kapasitas terhitung benar.
def test_valid_wav_passes(tmp_path):
    path = tmp_path / "ok.wav"
    _write_wav(path, n_samples=100_000)
    r = validate_one(path)
    assert r["valid"] is True
    assert r["capacity_total"] == 100_000 // 8
    assert r["capacity_payload"] == r["capacity_total"] - 10
    assert r["duration_sec"] == pytest.approx(100_000 / 44100, rel=1e-3)


#^ V2 — File tidak ada
# Verifikasi: path yang tidak ada -> valid=False, reason mengandung
# "tidak ditemukan".
def test_missing_file(tmp_path):
    r = validate_one(tmp_path / "tidak_ada.wav")
    assert r["valid"] is False
    assert "tidak ditemukan" in r["reason"]


#^ V3 — WAV 8-bit ditolak
# Verifikasi: WAV sampwidth=1 ditolak dengan reason yang jelas.
def test_8bit_wav_rejected(tmp_path):
    path = tmp_path / "8bit.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(1); w.setframerate(44100)
        w.writeframes(b"\x80" * 1000)
    r = validate_one(path)
    assert r["valid"] is False
    assert "PCM 16-bit" in r["reason"]


#^ V4 — Folder diekspansi ke semua *.wav
# Verifikasi: collect_files dengan input folder mengembalikan semua
# file .wav di dalamnya, terurut.
def test_collect_files_from_folder(tmp_path):
    _write_wav(tmp_path / "b.wav", n_samples=1000)
    _write_wav(tmp_path / "a.wav", n_samples=1000)
    (tmp_path / "ignore.txt").write_text("bukan wav")
    files = collect_files([tmp_path])
    assert len(files) == 2
    assert [f.name for f in files] == ["a.wav", "b.wav"]


#^ V5 — Kapasitas kurang untuk benchmark
# Verifikasi: WAV kecil (di bawah 2 MB kapasitas) tetap valid, tapi
# capacity_for_benchmark=False.
def test_small_wav_insufficient_for_benchmark(tmp_path):
    path = tmp_path / "kecil.wav"
    _write_wav(path, n_samples=10_000)  # kapasitas 1250 B, jauh di bawah 2 MB
    r = validate_one(path)
    assert r["valid"] is True
    assert r["capacity_for_benchmark"] is False