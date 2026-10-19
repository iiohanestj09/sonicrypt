"""
Audio steganography untuk Sonicrypt.
I/O file WAV PCM 16-bit.
"""
import wave
from pathlib import Path

import numpy as np


def read_wav(path) -> tuple[np.ndarray, dict]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"file tidak ditemukan: {path}")

    try:
        with wave.open(str(path), "rb") as w:
            nchannels = w.getnchannels()
            sampwidth = w.getsampwidth()
            framerate = w.getframerate()
            nframes = w.getnframes()
            comptype = w.getcomptype()
            compname = w.getcompname()
            frames = w.readframes(nframes)
    except wave.Error as e:
        raise ValueError(
            f"tidak bisa membaca WAV (mungkin bukan PCM): {e}"
        ) from e

    if comptype != "NONE":
        raise ValueError(
            f"format WAV terkompresi tidak didukung: comptype={comptype}"
        )
    if sampwidth != 2:
        raise ValueError(
            f"hanya mendukung PCM 16-bit (sampwidth=2), "
            f"dapat sampwidth={sampwidth}"
        )

    samples = np.frombuffer(frames, dtype=np.int16).copy()
    expected = nframes * nchannels
    if samples.size != expected:
        raise ValueError(
            f"panjang sample tidak konsisten: {samples.size} != {expected}"
        )

    params = {
        "nchannels": nchannels,
        "sampwidth": sampwidth,
        "framerate": framerate,
        "nframes": nframes,
        "comptype": comptype,
        "compname": compname,
    }
    return samples, params


def write_wav(path, samples, params) -> None:
    if not isinstance(samples, np.ndarray):
        raise TypeError(
            f"samples harus numpy array, dapat {type(samples).__name__}"
        )
    if samples.dtype != np.int16:
        raise TypeError(f"samples harus dtype int16, dapat {samples.dtype}")
    if samples.ndim != 1:
        raise ValueError(f"samples harus 1D, dapat {samples.ndim}D")

    nchannels = params["nchannels"]
    if samples.size % nchannels != 0:
        raise ValueError(
            f"jumlah sample ({samples.size}) tidak habis dibagi "
            f"nchannels ({nchannels})"
        )

    path = Path(path)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(nchannels)
        w.setsampwidth(params["sampwidth"])
        w.setframerate(params["framerate"])
        w.setcomptype(params["comptype"], params["compname"])
        w.writeframes(samples.tobytes())
        
def bytes_to_bits(data: bytes) -> np.ndarray:
    """
    Konversi bytes ke array bit uint8 (0/1), MSB-first.
    Contoh:
        b"\\x80" (1000_0000) -> [1,0,0,0,0,0,0,0]
        b"\\x01" (0000_0001) -> [0,0,0,0,0,0,0,1]
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"data harus bytes, dapat {type(data).__name__}")
    if len(data) == 0:
        return np.zeros(0, dtype=np.uint8)
    arr = np.frombuffer(bytes(data), dtype=np.uint8)
    return np.unpackbits(arr, bitorder="big")


def bits_to_bytes(bits: np.ndarray) -> bytes:
    bits = np.asarray(bits)
    if bits.ndim != 1:
        raise ValueError(f"bits harus 1D, dapat {bits.ndim}D")
    if bits.size % 8 != 0:
        raise ValueError(
            f"panjang bits harus kelipatan 8, dapat {bits.size}"
        )
    if bits.size == 0:
        return b""
    if not (np.issubdtype(bits.dtype, np.integer) or bits.dtype == np.bool_):
        raise TypeError(f"bits harus integer/bool, dapat {bits.dtype}")
    if bits.min() < 0 or bits.max() > 1:
        raise ValueError("bits harus berisi 0 atau 1")
    return np.packbits(bits.astype(np.uint8), bitorder="big").tobytes()


def embed_lsb(samples: np.ndarray, payload: bytes) -> np.ndarray:
    """
    Sisipkan payload ke LSB sample audio, MSB-first.
    Setiap sample menyumbang 1 bit kapasitas. Sample ke-i menerima
    bit ke-i dari payload. LSB sample lain tidak diubah.
    """
    if not isinstance(samples, np.ndarray):
        raise TypeError(f"samples harus numpy array, dapat {type(samples).__name__}")
    if samples.dtype != np.int16:
        raise TypeError(f"samples harus dtype int16, dapat {samples.dtype}")
    if samples.ndim != 1:
        raise ValueError(f"samples harus 1D, dapat {samples.ndim}D")
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError(f"payload harus bytes, dapat {type(payload).__name__}")

    bits = bytes_to_bits(payload)
    if bits.size > samples.size:
        raise ValueError(
            f"payload terlalu besar: butuh {bits.size} sample, "
            f"tersedia {samples.size}"
        )

    # View ke uint16 supaya operasi bitwise tidak terkena sign extension
    # int16 negatif. u adalah copy, jadi samples asli aman.
    s = np.ascontiguousarray(samples)
    u = s.view(np.uint16).copy()
    n = bits.size
    if n > 0:
        u[:n] = (u[:n] & np.uint16(0xFFFE)) | bits.astype(np.uint16)
    return u.view(np.int16)


def extract_lsb(samples: np.ndarray, nbytes: int) -> bytes:
    """
    Baca nbytes dari LSB samples, MSB-first.
    Invers dari embed_lsb: baca LSB dari sample[0..nbits-1], pack ke
    bytes. Kalau samples sudah berisi stego valid, hasilnya == payload
    asli.
    """
    if not isinstance(samples, np.ndarray):
        raise TypeError(f"samples harus numpy array, dapat {type(samples).__name__}")
    if samples.dtype != np.int16:
        raise TypeError(f"samples harus dtype int16, dapat {samples.dtype}")
    if samples.ndim != 1:
        raise ValueError(f"samples harus 1D, dapat {samples.ndim}D")
    if not isinstance(nbytes, int) or nbytes < 0:
        raise ValueError(f"nbytes harus int >= 0, dapat {nbytes!r}")

    nbits = nbytes * 8
    if nbits > samples.size:
        raise ValueError(
            f"nbytes terlalu besar: butuh {nbits} sample, "
            f"tersedia {samples.size}"
        )

    if nbits == 0:
        return b""

    # LSB dari int16 negatif tetap benar: -1 & 1 = 1, -2 & 1 = 0.
    bits = (samples[:nbits] & 1).astype(np.uint8)
    return bits_to_bytes(bits)