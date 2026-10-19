"""
Validasi file audio untuk Sonicrypt.

Mengecek apakah file WAV memenuhi syarat sebagai input sistem:
  - PCM 16-bit (sample width = 2 byte)
  - Tidak terkompresi (comptype = NONE)

Usage:
  python -m src.validate_audio input/Married_Life.wav
  python -m src.validate_audio input/                # semua *.wav di folder
  python -m src.validate_audio file1.wav file2.wav

Exit code 0 jika semua valid, 1 jika ada yang tidak valid.

TODO: python -m src.validate_audio input/music.wav
"""
import argparse
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BENCHMARK_MAX_BYTES = 2 * 1024 * 1024  # payload terbesar di benchmark
HEADER_BYTES = 10                       # pipeline.HEADER_SIZE

# Warna ANSI, dimatikan otomatis kalau stdout bukan TTY
if sys.stdout.isatty():
    C_OK, C_WARN, C_ERR, C_DIM, C_RST = "\033[92m", "\033[93m", "\033[91m", "\033[2m", "\033[0m"
else:
    C_OK = C_WARN = C_ERR = C_DIM = C_RST = ""


def fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def fmt_duration(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m}m {s:02d}s"


def get_metadata(path: Path) -> dict:
    """Ambil metadata WAV dari header saja (tanpa load seluruh sample)."""
    try:
        with wave.open(str(path), "rb") as w:
            return {
                "nchannels": w.getnchannels(),
                "sampwidth": w.getsampwidth(),
                "framerate": w.getframerate(),
                "nframes": w.getnframes(),
                "comptype": w.getcomptype(),
                "compname": w.getcompname(),
            }
    except wave.Error as e:
        raise ValueError(f"tidak bisa membaca WAV: {e}") from e


def diagnose_with_soundfile(path: Path) -> str:
    """Kalau wave.open gagal, cek format aktual via soundfile untuk diagnosa."""
    try:
        import soundfile as sf
        info = sf.info(str(path))
        return f"{info.format}/{info.subtype}, {info.samplerate} Hz, {info.channels} ch"
    except ImportError:
        return "(soundfile tidak terinstall, tidak bisa diagnosa lanjutan)"
    except Exception as e:
        return f"(soundfile juga gagal: {e})"


def validate_one(path: Path) -> dict:
    """Validasi satu file. Return dict status + info."""
    result = {"path": str(path), "valid": False, "reason": None, "actual": None}

    if not path.exists():
        result["reason"] = "file tidak ditemukan"
        return result
    if not path.is_file():
        result["reason"] = "bukan file (mungkin folder)"
        return result

    try:
        meta = get_metadata(path)
    except ValueError as e:
        result["reason"] = str(e)
        result["actual"] = diagnose_with_soundfile(path)
        return result

    if meta["sampwidth"] != 2:
        result["reason"] = (
            f"bukan PCM 16-bit: sampwidth={meta['sampwidth']} byte "
            f"({meta['sampwidth'] * 8}-bit)"
        )
        result["actual"] = diagnose_with_soundfile(path)
        return result

    if meta["comptype"] != "NONE":
        result["reason"] = (
            f"WAV terkompresi tidak didukung: comptype={meta['comptype']}"
        )
        result["actual"] = diagnose_with_soundfile(path)
        return result

    n_samples = meta["nframes"] * meta["nchannels"]
    cap_total = n_samples // 8
    cap_payload = cap_total - HEADER_BYTES
    duration = meta["nframes"] / meta["framerate"]

    result["valid"] = True
    result["meta"] = meta
    result["capacity_total"] = cap_total
    result["capacity_payload"] = cap_payload
    result["capacity_for_benchmark"] = cap_payload >= BENCHMARK_MAX_BYTES
    result["duration_sec"] = duration
    return result


def print_report(result: dict) -> None:
    path = result["path"]
    print(f"\n{C_DIM}{'-' * 64}{C_RST}")
    print(f"File: {path}")
    print(f"{C_DIM}{'-' * 64}{C_RST}")

    if not result["valid"]:
        print(f"{C_ERR}❌ TIDAK VALID{C_RST}")
        print(f"   Alasan: {result['reason']}")
        if result["actual"]:
            print(f"   Format aktual: {result['actual']}")
        print()
        out = Path(path).stem + "_pcm16.wav"
        print("   Konversi ke PCM 16-bit dengan ffmpeg:")
        print(f'   {C_DIM}ffmpeg -i "{path}" -c:a pcm_s16le -ar 48000 -ac 2 "{out}"{C_RST}')
        return

    m = result["meta"]
    ch = {1: "mono", 2: "stereo"}.get(m["nchannels"], f"{m['nchannels']} channel")
    print(f"{C_OK}✅ VALID{C_RST} — siap dipakai sebagai input Sonicrypt")
    print()
    print(f"   Format      : WAV PCM 16-bit, tidak terkompresi")
    print(f"   Channels    : {m['nchannels']} ({ch})")
    print(f"   Sample rate : {m['framerate']} Hz")
    print(f"   Durasi      : {fmt_duration(result['duration_sec'])} ({result['duration_sec']:.2f} detik)")
    print(f"   Frames      : {m['nframes']:,}")
    print()
    print(f"   Kapasitas total   : {fmt_bytes(result['capacity_total'])}")
    print(f"   Kapasitas payload : {fmt_bytes(result['capacity_payload'])} (setelah header {HEADER_BYTES} B)")

    if result["capacity_for_benchmark"]:
        print(f"   Benchmark (2 MB)  : {C_OK}✅ cukup{C_RST}")
    else:
        gap = BENCHMARK_MAX_BYTES - result["capacity_payload"]
        print(f"   Benchmark (2 MB)  : {C_WARN}⚠️  kurang {fmt_bytes(gap)}{C_RST}")
        print(f"   Payload terbesar yang bisa diuji: {fmt_bytes(result['capacity_payload'])}")


def collect_files(paths: list[Path]) -> list[Path]:
    """Ekspansi folder menjadi daftar file .wav di dalamnya."""
    files = []
    for p in paths:
        if p.is_dir():
            found = sorted(p.glob("*.wav"))
            if not found:
                print(f"{C_WARN}⚠️  Folder {p} tidak berisi file .wav{C_RST}")
            files.extend(found)
        else:
            files.append(p)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validasi file audio WAV untuk Sonicrypt",
    )
    parser.add_argument(
        "paths", nargs="+", type=Path,
        help="Path ke file atau folder (folder = semua *.wav di dalamnya)",
    )
    args = parser.parse_args()

    files = collect_files(args.paths)
    if not files:
        print("Tidak ada file untuk divalidasi.")
        return 1

    results = [validate_one(f) for f in files]
    for r in results:
        print_report(r)

    n_valid = sum(1 for r in results if r["valid"])
    n_total = len(results)
    color = C_OK if n_valid == n_total else C_ERR
    print(f"\n{color}Ringkasan: {n_valid}/{n_total} file valid{C_RST}")

    return 0 if n_valid == n_total else 1


if __name__ == "__main__":
    sys.exit(main())