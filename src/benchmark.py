"""
Benchmark Sonicrypt: 10 payload ukuran berbeda pada audio asli.

Jalankan sebagai script:
    python -m src.benchmark

Atau import:
    from src.benchmark import run_benchmark
    df = run_benchmark("input/married_life.wav" "benchmark")

Output:
    output/benchmark_results.csv   -> tabel hasil
    output/benchmark_charts.png    -> grafik 2x2
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.metrics import sha256
from src.pipeline import embed, extract

DEFAULT_SIZES = [
    16, 64, 256, 1024, 4096, 16384, 65536, 262144, 1048576, 2097152,
]

COLUMNS = [
    "size_label", "size_B", "plaintext_bytes", "payload_bytes",
    "capacity_bytes", "capacity_pct",
    "encrypt_core_ms", "embed_core_ms", "extract_core_ms", "decrypt_core_ms",
    "embed_total_ms", "extract_total_ms",
    "mse", "snr_db", "hash_match", "status",
]


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def _make_plaintext(size: int) -> bytes:
    """Payload reproducible: pola deterministik, bukan acak."""
    return bytes((i * 31 + 7) & 0xFF for i in range(size))


def run_benchmark(
    audio_input,
    passphrase: str,
    sizes: list[int] | None = None,
    output_csv=None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Jalankan benchmark untuk setiap ukuran payload.

    Setiap iterasi: embed -> extract -> verifikasi hash -> catat metrik.
    Kalau satu payload gagal, dicatat sebagai FAILED dan loop lanjut.

    Returns
    -------
    pd.DataFrame dengan kolom sesuai COLUMNS.
    """
    sizes = sizes or DEFAULT_SIZES
    rows = []

    for size in sizes:
        plaintext = _make_plaintext(size)
        label = _fmt_size(size)

        if verbose:
            print(f"[{label:>7}] embedding...", end=" ", flush=True)

        try:
            t0 = time.perf_counter()
            stego_bytes, info_embed = embed(audio_input, plaintext, passphrase)
            embed_total_ms = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            recovered, info_extract = extract(stego_bytes, passphrase)
            extract_total_ms = (time.perf_counter() - t0) * 1000

            hash_ok = sha256(plaintext) == sha256(recovered)
            status = "OK" if hash_ok else "HASH_MISMATCH"

            row = {
                "size_label": label,
                "size_B": size,
                "plaintext_bytes": len(plaintext),
                "payload_bytes": info_embed["payload_bytes"],
                "capacity_bytes": info_embed["capacity_bytes"],
                "capacity_pct": info_embed["payload_bytes"]
                / info_embed["capacity_bytes"] * 100,
                "encrypt_core_ms": info_embed["encrypt_time_s"] * 1000,
                "embed_core_ms": info_embed["embed_time_s"] * 1000,
                "extract_core_ms": info_extract["extract_time_s"] * 1000,
                "decrypt_core_ms": info_extract["decrypt_time_s"] * 1000,
                "embed_total_ms": embed_total_ms,
                "extract_total_ms": extract_total_ms,
                "mse": info_embed["mse"],
                "snr_db": info_embed["snr_db"],
                "hash_match": hash_ok,
                "status": status,
            }
            if verbose:
                print(
                    f"SNR={info_embed['snr_db']:6.2f} dB  "
                    f"embed={embed_total_ms:7.1f} ms  "
                    f"extract={extract_total_ms:7.1f} ms  "
                    f"{'OK' if hash_ok else 'MISMATCH'}"
                )

        except Exception as e:
            if verbose:
                print(f"FAILED: {type(e).__name__}: {e}")
            row = {col: None for col in COLUMNS}
            row["size_label"] = label
            row["size_B"] = size
            row["status"] = f"FAILED: {type(e).__name__}"
            row["hash_match"] = False

        rows.append(row)

    df = pd.DataFrame(rows, columns=COLUMNS)

    if output_csv is not None:
        out = Path(output_csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)
        if verbose:
            print(f"\nCSV tersimpan: {out}")

    return df


def plot_benchmark(df: pd.DataFrame, output_path, title="Sonicrypt Benchmark") -> None:
    """Simpan grafik 2x2: SNR, waktu, kapasitas, MSE per payload."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Filter out failed rows so plot doesn't crash
    ok = df[df["status"] == "OK"].copy()
    if ok.empty:
        raise ValueError("tidak ada baris OK untuk di-plot")

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    x = np.arange(len(ok))
    labels = ok["size_label"].tolist()

    # (0,0) SNR
    ax = axes[0, 0]
    ax.bar(x, ok["snr_db"], color="#2E86AB")
    ax.set_title("Signal-to-Noise Ratio")
    ax.set_ylabel("SNR (dB)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.3)

    # (0,1) Waktu
    ax = axes[0, 1]
    ax.bar(x - 0.2, ok["embed_total_ms"], width=0.4, label="Embed", color="#2E86AB")
    ax.bar(x + 0.2, ok["extract_total_ms"], width=0.4, label="Extract", color="#E67E22")
    ax.set_title("Total Time (embed vs extract)")
    ax.set_ylabel("Time (ms, log scale)")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    # (1,0) Kapasitas
    ax = axes[1, 0]
    ax.bar(x, ok["capacity_pct"], color="#27AE60")
    ax.set_title("Capacity Utilization")
    ax.set_ylabel("Capacity used (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.3)

    # (1,1) MSE
    ax = axes[1, 1]
    ax.plot(x, ok["mse"], marker="o", color="#C0392B", linewidth=2)
    ax.set_title("Mean Squared Error")
    ax.set_ylabel("MSE (log scale)")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Grafik tersimpan: {out}")


def main() -> int:
    input_path = Path("input/married_life.wav")
    if not input_path.exists():
        print(f"ERROR: {input_path} tidak ditemukan")
        print("Taruh WAV PCM 16-bit di path tersebut, atau panggil run_benchmark() langsung.")
        return 1

    df = run_benchmark(
        input_path,
        passphrase="benchmark",
        output_csv="output/benchmark_results.csv",
        verbose=True,
    )

    print()
    print(df[["size_label", "snr_db", "mse",
              "embed_total_ms", "extract_total_ms", "status"]].to_string(index=False))

    plot_benchmark(df, "output/benchmark_charts.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())