"""
Test untuk src/benchmark.py.

Jalankan: pytest tests/benchmark_test.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import pytest

from src.benchmark import run_benchmark, plot_benchmark, COLUMNS
from src.stego import wav_bytes


def _make_audio_wav(n_samples=100_000, seed=42) -> bytes:
    """Audio sintetis 100k sample -> ~12.5 KB kapasitas payload."""
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


#^ B1 — Struktur DataFrame
# Verifikasi: kolom sesuai COLUMNS, jumlah baris sesuai len(sizes),
# dan semua baris sukses (hash_match=True, status="OK").
def test_benchmark_dataframe_shape():
    audio = _make_audio_wav(100_000)
    sizes = [16, 64, 256, 1024]
    df = run_benchmark(audio, "abc", sizes=sizes, verbose=False)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == COLUMNS
    assert len(df) == len(sizes)
    assert (df["status"] == "OK").all()
    assert df["hash_match"].all()


#^ B2 — CSV tertulis saat output_csv diisi
# Verifikasi: file CSV dibuat, dan isinya bisa dibaca kembali
# dengan shape yang sama.
def test_benchmark_writes_csv(tmp_path):
    audio = _make_audio_wav(100_000)
    out = tmp_path / "hasil.csv"
    df = run_benchmark(audio, "abc", sizes=[16, 64], output_csv=out, verbose=False)

    assert out.exists()
    df2 = pd.read_csv(out)
    assert len(df2) == len(df)
    assert list(df2.columns) == COLUMNS


#^ B3 — Payload terlalu besar dicatat sebagai FAILED
# Verifikasi: size yang melebihi kapasitas menghasilkan baris dengan
# status FAILED, bukan raise exception, dan tidak crash.
def test_benchmark_records_failure():
    audio = _make_audio_wav(1000)  # 125 byte kapasitas total
    df = run_benchmark(audio, "abc", sizes=[16, 500], verbose=False)

    assert len(df) == 2
    assert df.iloc[0]["status"] == "OK"
    assert "FAILED" in df.iloc[1]["status"]


#^ B4 — Plot menghasilkan file PNG
# Verifikasi: grafik 2x2 tersimpan sebagai PNG, ukurannya > 0.
def test_plot_benchmark(tmp_path):
    audio = _make_audio_wav(100_000)
    df = run_benchmark(audio, "abc", sizes=[16, 64, 256], verbose=False)

    out = tmp_path / "chart.png"
    plot_benchmark(df, out)
    assert out.exists()
    assert out.stat().st_size > 1000  # PNG valid minimal > 1 KB