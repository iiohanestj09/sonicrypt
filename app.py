import sys
import io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st
import soundfile as sf
from cryptography.exceptions import InvalidTag

from src.pipeline import embed, extract, HEADER_SIZE
from src.stego import read_wav_bytes
from src.metrics import capacity_bytes

st.set_page_config(page_title="Sonicrypt", page_icon="🎵", layout="wide")

# Inisialisasi versi uploader untuk fitur reset
if "uploader_version" not in st.session_state:
    st.session_state["uploader_version"] = 0

st.title("🎵 Sonicrypt")
st.caption("Audio Dead-Drop — AES-GCM + LSB pada Audio WAV")
st.markdown("---")

tab_validate, tab_kirim, tab_terima, tab_uji = st.tabs([
    "🔍 Validasi Audio",
    "📤 Kirim Pesan",
    "📥 Terima Pesan",
    "📊 Hasil Uji",
])


def _fmt_capacity(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


# =====================================================================
# TAB 1 — VALIDASI AUDIO
# =====================================================================
with tab_validate:
    st.header("Validasi Audio Sebelum Digunakan")
    st.write(
        "Upload WAV untuk memastikan formatnya cocok. "
        "Sonicrypt hanya menerima **WAV PCM 16-bit tidak terkompresi**."
    )

    uploaded = st.file_uploader(
        "Upload Audio (WAV)", type=["wav"], 
        key=f"validate_uploader_{st.session_state['uploader_version']}"
    )

    if uploaded is not None:
        audio_bytes = uploaded.read()
        uploaded.seek(0)

        valid = False
        info = None
        error_reason = None

        try:
            samples, params = read_wav_bytes(audio_bytes)
            cap_payload = capacity_bytes(samples) - HEADER_SIZE
            dur_sec = params["nframes"] / params["framerate"]
            info = {
                "nchannels": params["nchannels"],
                "framerate": params["framerate"],
                "duration_sec": round(dur_sec, 2),
                "capacity_payload": cap_payload,
            }
            valid = True
        except (ValueError, TypeError) as e:
            error_reason = str(e)

        if valid:
            st.success("✅ Audio valid — siap digunakan")

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Channels", info["nchannels"])
            col_b.metric("Sample rate", f"{info['framerate']} Hz")
            col_c.metric("Durasi", f"{info['duration_sec']} s")

            st.info(
                f"Kapasitas payload: **{_fmt_capacity(info['capacity_payload'])}** "
                f"({info['capacity_payload']:,} byte)"
            )

            st.audio(audio_bytes, format="audio/wav")

            # Simpan ke session_state untuk dipakai di Tab 2
            st.session_state["validated_audio_bytes"] = audio_bytes
            st.session_state["validated_audio_name"] = uploaded.name
            st.session_state["validated_audio_info"] = info

            st.success(
                f"Audio **{uploaded.name}** disimpan. Lanjut ke tab **📤 Kirim Pesan**."
            )

        else:
            st.error(f"❌ Audio tidak valid: {error_reason}")

            # Diagnosa via soundfile
            try:
                sf_info = sf.info(io.BytesIO(audio_bytes))
                st.caption(
                    f"Format aktual: **{sf_info.format} / {sf_info.subtype}** · "
                    f"{sf_info.samplerate} Hz · {sf_info.channels} ch"
                )
            except Exception:
                st.caption("Format aktual: tidak dikenali oleh soundfile.")

            st.markdown("### Konversi ke PCM 16-bit")

            # --- Coba konversi otomatis via soundfile ---
            with st.spinner("Mencoba konversi otomatis..."):
                try:
                    data, sr = sf.read(io.BytesIO(audio_bytes))
                    buf = io.BytesIO()
                    sf.write(buf, data, sr, format="WAV", subtype="PCM_16")
                    converted = buf.getvalue()

                    # Verifikasi hasil konversi benar-benar PCM 16-bit
                    read_wav_bytes(converted)

                    st.success(
                        "✅ Konversi otomatis berhasil — hasil sudah WAV PCM 16-bit."
                    )
                    st.audio(converted, format="audio/wav")
                    st.download_button(
                        label="⬇️ Unduh WAV PCM 16-bit",
                        data=converted,
                        file_name=f"pcm16_{uploaded.name}",
                        mime="audio/wav",
                        key="download_converted",
                    )
                    st.caption(
                        "Setelah diunduh, upload ulang file hasil konversi di atas "
                        "untuk verifikasi, lalu gunakan di tab **Kirim Pesan**."
                    )

                except Exception as e:
                    st.warning(f"Konversi otomatis gagal: {e}")
                    st.write("Gunakan **ffmpeg** di terminal:")
                    out_name = Path(uploaded.name).stem + "_pcm16.wav"
                    st.code(
                        f'ffmpeg -i "{uploaded.name}" -c:a pcm_s16le -ar 48000 -ac 2 "{out_name}"',
                        language="bash",
                    )
                    st.caption(
                        "Install ffmpeg: `winget install ffmpeg` (Windows) atau "
                        "`brew install ffmpeg` (macOS), atau `sudo apt install ffmpeg` (Linux)."
                    )


# =====================================================================
# TAB 2 — KIRIM PESAN
# =====================================================================
with tab_kirim:
    st.header("Sembunyikan Pesan dalam Audio")

    validated_bytes = st.session_state.get("validated_audio_bytes")
    validated_name = st.session_state.get("validated_audio_name")

    audio_bytes = None
    source_name = None

    if validated_bytes is not None:
        st.success(f"✅ Menggunakan audio tervalidasi: **{validated_name}**")
        st.audio(validated_bytes, format="audio/wav")
        if st.button("🔄 Ganti audio", key="reset_audio"):
            st.session_state.pop("validated_audio_bytes", None)
            st.session_state.pop("validated_audio_name", None)
            st.session_state.pop("validated_audio_info", None)
            st.session_state["uploader_version"] += 1
            st.rerun()
        audio_bytes = validated_bytes
        source_name = validated_name
    else:
        st.info(
            "Belum ada audio tervalidasi. Upload di sini, atau gunakan tab "
            "**🔍 Validasi Audio** untuk diagnosa lebih lengkap."
        )

    col1, col2 = st.columns([1, 1])

    with col1:
        # Kalau belum ada audio tervalidasi, tampilkan uploader
        if audio_bytes is None:
            uploaded_kirim = st.file_uploader(
                "Upload Audio (WAV PCM 16-bit)", type=["wav"], 
                key=f"kirim_uploader_{st.session_state['uploader_version']}"
            )
            if uploaded_kirim is not None:
                raw = uploaded_kirim.read()
                uploaded_kirim.seek(0)
                try:
                    samples, params = read_wav_bytes(raw)
                    cap = capacity_bytes(samples) - HEADER_SIZE
                    st.success(f"✅ Audio valid — kapasitas {_fmt_capacity(cap)}")
                    audio_bytes = raw
                    source_name = uploaded_kirim.name
                except (ValueError, TypeError) as e:
                    st.error(f"❌ Audio tidak valid: {e}")
                    audio_bytes = None

        pesan = st.text_area(
            "Pesan Rahasia",
            placeholder="Ketik pesan yang ingin disembunyikan...",
            key="kirim_pesan",
        )
        passphrase = st.text_input(
            "Passphrase", type="password", key="kirim_key"
        )

        # Peringatan awal kalau pesan melebihi kapasitas
        if audio_bytes is not None and pesan:
            samples_c, _ = read_wav_bytes(audio_bytes)
            cap = capacity_bytes(samples_c) - HEADER_SIZE
            pesan_len = len(pesan.encode("utf-8"))
            if pesan_len > cap:
                st.warning(
                    f"⚠️ Pesan ({pesan_len} B) melebihi kapasitas "
                    f"({_fmt_capacity(cap)})"
                )

        btn_embed = st.button(
            "🔒 Sisipkan & Unduh Audio",
            type="primary",
            use_container_width=True,
            disabled=audio_bytes is None,
        )

    with col2:
        if btn_embed:
            if not audio_bytes or not pesan or not passphrase:
                st.error("Audio, pesan, dan passphrase wajib diisi!")
            else:
                with st.spinner("Memproses..."):
                    try:
                        stego_bytes, info = embed(
                            audio_bytes, pesan.encode(), passphrase
                        )
                        st.success("Pesan berhasil disisipkan!")

                        st.write("**Audio Asli:**")
                        st.audio(audio_bytes, format="audio/wav")
                        st.write("**Audio Stego (Hasil):**")
                        st.audio(stego_bytes, format="audio/wav")

                        st.download_button(
                            label="⬇️ Unduh Audio Stego",
                            data=stego_bytes,
                            file_name=f"stego_{source_name or 'audio.wav'}",
                            mime="audio/wav",
                            key="download_stego",
                        )
                        st.json(info)
                    except Exception as e:
                        st.error(f"Gagal: {e}")


# =====================================================================
# TAB 3 — TERIMA PESAN (sama seperti sebelumnya)
# =====================================================================
with tab_terima:
    st.header("Ekstrak Pesan dari Audio")

    col1, col2 = st.columns([1, 1])

    with col1:
        stego_file = st.file_uploader(
            "Upload Audio Stego", type=["wav"], key="terima_uploader"
        )
        passphrase_ext = st.text_input(
            "Passphrase", type="password", key="terima_key",
            placeholder="Kunci dekripsi...",
        )
        btn_extract = st.button(
            "🔓 Ekstrak Pesan", type="primary", use_container_width=True
        )

    with col2:
        if btn_extract:
            if not stego_file or not passphrase_ext:
                st.error("Audio dan passphrase wajib diisi!")
            else:
                with st.spinner("Mengekstrak dan mendekripsi..."):
                    try:
                        stego_bytes = stego_file.read()
                        plaintext, info = extract(stego_bytes, passphrase_ext)
                        st.success("Pesan berhasil diekstrak!")
                        st.text_area(
                            "Pesan Rahasia:",
                            value=plaintext.decode("utf-8", errors="replace"),
                            height=150,
                        )
                        st.json(info)
                    except InvalidTag:
                        st.error(
                            "❌ Gagal: Passphrase salah, atau audio telah "
                            "dimodifikasi/dirusak."
                        )
                    except ValueError as e:
                        st.error(f"❌ Gagal: {e}")
                    except Exception as e:
                        st.error(f"❌ Error tidak terduga: {e}")


# =====================================================================
# TAB 4 — HASIL UJI (sama seperti sebelumnya)
# =====================================================================
with tab_uji:
    st.header("Benchmark: 10 Payload pada Audio Asli")
    st.write(
        "Data ini di-generate dari `python -m src.benchmark` pada `input/married_life.wav`."
    )

    csv_path = Path("output/benchmark_results.csv")
    img_path = Path("output/benchmark_charts.png")

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        st.dataframe(
            df[[
                "size_label", "snr_db", "mse",
                "embed_total_ms", "extract_total_ms", "status",
            ]],
            use_container_width=True,
        )
    else:
        st.warning(
            "File CSV belum ada. Jalankan `python -m src.benchmark` terlebih dahulu."
        )

    if img_path.exists():
        st.image(str(img_path), caption="Grafik Benchmark", use_container_width=True)
    else:
        st.warning(
            "File grafik belum ada. Jalankan `python -m src.benchmark` terlebih dahulu."
        )

    st.markdown("---")
    st.subheader("Robustness Test")
    robust_path = Path("output/robustness_results.csv")
    if robust_path.exists():
        df_r = pd.read_csv(robust_path)
        st.dataframe(df_r, use_container_width=True)
        st.caption(
            "Baris dengan status **GAGAL (Aman)** membuktikan sistem mendeteksi "
            "manipulasi audio dan menolak data rusak."
        )
    else:
        st.info(
            "Belum ada data robustness. Jalankan `python -m src.robustness`."
        )