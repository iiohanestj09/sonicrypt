import sys
import io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import soundfile as sf
from cryptography.exceptions import InvalidTag

from src.pipeline import embed, extract, HEADER_SIZE
from src.stego import read_wav_bytes
from src.metrics import capacity_bytes

st.set_page_config(
    page_title="Sonicrypt — Audio Dead-Drop",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --accent: #c62828;
    --accent-dark: #a3151a;
    --accent-soft: #fff1f1;
    --ink: #242124;
    --muted: #746d70;
    --line: #eee5e5;
    --surface: #ffffff;
    --shadow-card: 0 10px 30px rgba(77, 26, 26, 0.07), 0 2px 6px rgba(77, 26, 26, 0.04);
}

html, body, [class*="css"], button, input, textarea {
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: #ffffff !important;
    color: var(--ink);
}
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding: 1.5rem 2rem 3.5rem; max-width: 1320px;}

/* Hero */
.hero {
    position: relative;
    overflow: hidden;
    text-align: center;
    padding: 46px 24px 40px;
    margin: 0 0 28px;
    border: 1px solid #f1dddd;
    border-radius: 26px;
    background: radial-gradient(ellipse at 50% -35%, #ffe4e4 0%, #fff8f8 48%, #ffffff 82%);
    box-shadow: 0 14px 36px rgba(128, 25, 25, 0.07);
}
.hero::before, .hero::after {
    content: "";
    position: absolute;
    width: 180px;
    height: 180px;
    border: 1px solid rgba(198, 40, 40, 0.10);
    border-radius: 50%;
    pointer-events: none;
}
.hero::before {top: -112px; left: 8%;}
.hero::after {right: 8%; bottom: -132px; width: 220px; height: 220px;}
.hero-title {
    position: relative;
    z-index: 1;
    font-family: 'Space Grotesk', 'DM Sans', sans-serif;
    font-size: clamp(3rem, 7vw, 5rem);
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -0.065em;
    line-height: 1;
    margin: 0;
}
.hero-subtitle {
    position: relative;
    z-index: 1;
    color: #65585a;
    font-size: 1.05rem;
    margin: 16px auto 0;
    font-weight: 500;
}
.hero-badge {
    position: relative;
    z-index: 1;
    display: inline-block;
    padding: 8px 16px;
    background: #ffffff;
    border: 1px solid #efcaca;
    border-radius: 100px;
    color: var(--accent-dark);
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.035em;
    margin-top: 20px;
    box-shadow: 0 3px 10px rgba(128, 25, 25, 0.06);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    display: flex !important;
    align-items: stretch;
    width: 100%;
    box-sizing: border-box;
    gap: 6px;
    padding: 7px;
    border: 1px solid var(--line);
    border-radius: 16px;
    background: #faf8f8;
    box-shadow: 0 4px 14px rgba(45, 25, 25, 0.04);
}
.stTabs [data-baseweb="tab"] {
    flex: 1 1 0%;
    justify-content: center;
    min-width: 0;
    height: 48px;
    padding: 0 12px;
    border-radius: 11px;
    color: #655d5f;
    font-size: 0.94rem;
    font-weight: 700;
    white-space: nowrap;
    transition: color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--accent);
    background: #fff0f0;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #cf3333, #ad171d);
    color: #ffffff !important;
    box-shadow: 0 5px 13px rgba(174, 25, 31, 0.22);
}
.stTabs [data-baseweb="tab-highlight"] {background-color: transparent;}

/* Bordered containers as elevated cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    position: relative;
    border: 1px solid var(--line) !important;
    border-radius: 18px !important;
    background: var(--surface) !important;
    box-shadow: var(--shadow-card);
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #e9c4c4 !important;
    box-shadow: 0 14px 34px rgba(77, 26, 26, 0.10), 0 3px 8px rgba(77, 26, 26, 0.04);
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    color: var(--ink) !important;
    font-family: 'Space Grotesk', 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.035em;
}
h2, h3 {margin-bottom: 0.35rem !important;}
[data-testid="stCaptionContainer"] {color: var(--muted);}

/* Buttons */
.stButton > button, .stDownloadButton > button {
    min-height: 44px;
    border: 1px solid #eadada !important;
    border-radius: 12px !important;
    background: #ffffff !important;
    color: #4a3638 !important;
    font-weight: 700 !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease !important;
    box-shadow: 0 3px 9px rgba(65, 24, 24, 0.06) !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px);
    border-color: #d98989 !important;
    box-shadow: 0 8px 18px rgba(140, 30, 30, 0.12) !important;
    color: var(--accent-dark) !important;
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    border: 1px solid var(--accent) !important;
    background: linear-gradient(135deg, #d83b3b 0%, #b51e25 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 6px 15px rgba(181, 30, 37, 0.22) !important;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
    border-color: #99151b !important;
    box-shadow: 0 9px 20px rgba(181, 30, 37, 0.30) !important;
}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
    outline: 3px solid rgba(198, 40, 40, 0.22) !important;
    outline-offset: 2px;
}

/* Form controls */
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div {
    border-radius: 11px !important;
    border-color: #e8dddd !important;
    background: #ffffff !important;
    color: var(--ink) !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #cf5555 !important;
    box-shadow: 0 0 0 3px rgba(198, 40, 40, 0.10) !important;
}
.stTextInput label, .stTextArea label, [data-testid="stFileUploader"] label {
    color: #453b3d !important;
    font-weight: 700 !important;
}

/* File uploader */
[data-testid="stFileUploader"] > section {
    border: 1.5px dashed #e4baba !important;
    border-radius: 14px !important;
    background: linear-gradient(145deg, #fffafa, #fff4f4) !important;
    transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stFileUploader"] > section:hover {
    border-color: var(--accent) !important;
    background: #fff0f0 !important;
    box-shadow: 0 5px 14px rgba(160, 30, 30, 0.07);
}
[data-testid="stFileUploader"] button {
    border-radius: 9px !important;
    border-color: #e4baba !important;
    background: #ffffff !important;
    color: var(--accent-dark) !important;
    font-weight: 700 !important;
}

/* Metrics */
[data-testid="stMetric"] {
    padding: 15px 17px;
    border: 1px solid #f0e5e5;
    border-radius: 14px;
    background: linear-gradient(145deg, #ffffff, #fffafa);
    box-shadow: 0 4px 12px rgba(77, 26, 26, 0.04);
}
[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: var(--accent-dark) !important;
    font-family: 'Space Grotesk', 'DM Sans', sans-serif !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
}

/* Alerts, expanders, tables, and media */
div[data-testid="stAlert"] {
    border-radius: 13px !important;
    border: 1px solid #f0e4e4 !important;
    box-shadow: 0 3px 10px rgba(77, 26, 26, 0.04);
}
[data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: 13px !important;
    background: #ffffff;
    overflow: hidden;
}
[data-testid="stExpander"] summary:hover {color: var(--accent-dark);}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--line);
    border-radius: 12px;
    overflow: hidden;
}
[data-testid="stAudio"] {border-radius: 13px;}

/* Download caption under button */
.dl-hint {
    color: var(--muted);
    font-size: 0.82rem;
    margin-top: 6px;
    text-align: center;
}

@media (max-width: 700px) {
    .block-container {padding: 1rem 1rem 2.5rem;}
    .hero {padding: 36px 16px 30px; border-radius: 20px;}
    .hero-subtitle {font-size: 0.95rem;}
    .stTabs [data-baseweb="tab-list"] {
        justify-content: flex-start;
        overflow-x: auto;
        scrollbar-width: thin;
        scrollbar-color: #d99a9a #faf8f8;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 0 0 auto;
        min-width: max-content;
        height: 44px;
        padding: 0 12px;
        font-size: 0.82rem;
    }
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================
def _fmt_capacity(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def _auto_open_uploader_in_tab() -> None:
    components.html("""
    <script>
    setTimeout(function() {
        var uploaders = window.parent.document.querySelectorAll('[data-testid="stFileUploader"]');
        for (var i = 0; i < uploaders.length; i++) {
            var u = uploaders[i];
            if (!u.offsetParent) continue;
            var btn = u.querySelector('button');
            if (btn) { btn.click(); return; }
        }
    }, 250);
    </script>
    """, height=0)


def _notify_on_download(button_text: str = "Unduh Audio Stego") -> None:
    """Attach JS toast saat tombol download diklik."""
    components.html(f"""
    <script>
    setTimeout(function() {{
        var parent = window.parent.document;
        var buttons = parent.querySelectorAll('button');
        for (var i = 0; i < buttons.length; i++) {{
            if (buttons[i].textContent.includes('{button_text}') && !buttons[i].dataset.toastAttached) {{
                buttons[i].dataset.toastAttached = '1';
                buttons[i].addEventListener('click', function() {{
                    var toast = parent.createElement('div');
                    toast.setAttribute('role', 'status');
                    toast.style.cssText = 'position: fixed; bottom: 32px; right: 32px; display: flex; align-items: center; gap: 12px; background: linear-gradient(135deg, #cf3333, #a3151a); color: white; padding: 14px 16px 14px 20px; border-radius: 14px; box-shadow: 0 12px 32px rgba(100,20,20,0.28); font-weight: 600; font-size: 15px; z-index: 999999; font-family: "DM Sans", sans-serif; transition: opacity 0.4s;';
                    var message = parent.createElement('span');
                    message.textContent = '📥 Download dimulai — cek folder Download';
                    var closeButton = parent.createElement('button');
                    closeButton.type = 'button';
                    closeButton.textContent = '×';
                    closeButton.setAttribute('aria-label', 'Tutup notifikasi download');
                    closeButton.style.cssText = 'border: 0; background: transparent; color: white; cursor: pointer; font-size: 24px; line-height: 1; padding: 0 2px;';
                    toast.appendChild(message);
                    toast.appendChild(closeButton);
                    parent.body.appendChild(toast);
                    var dismissTimer;
                    function dismissToast() {{
                        parent.clearTimeout(dismissTimer);
                        toast.style.opacity = '0';
                        parent.setTimeout(function() {{ toast.remove(); }}, 400);
                    }}
                    closeButton.addEventListener('click', dismissToast);
                    dismissTimer = parent.setTimeout(dismissToast, 3000);
                }});
                break;
            }}
        }}
    }}, 500);
    </script>
    """, height=0)


# Session state
if "uploader_version" not in st.session_state:
    st.session_state["uploader_version"] = 0


# =====================================================================
# HERO HEADER
# =====================================================================
st.markdown("""
<div class="hero">
    <div class="hero-title">🎵 Sonicrypt</div>
    <p class="hero-subtitle">Sembunyikan pesan rahasia dalam audio — terenkripsi, tidak terlihat, tidak terdengar.</p>
    <span class="hero-badge">AES-256-GCM · LSB Audio Steganography</span>
</div>
""", unsafe_allow_html=True)


# =====================================================================
# TABS
# =====================================================================
tab_validate, tab_kirim, tab_terima, tab_uji = st.tabs([
    "🔍  Validasi",
    "📤  Kirim Pesan",
    "📥  Terima Pesan",
    "📊  Hasil Uji",
])


# =====================================================================
# TAB 1 — VALIDASI
# =====================================================================
with tab_validate:
    st.markdown("### 🔍 Validasi Audio")
    st.caption("Pastikan WAV yang kamu upload kompatibel sebelum disembunyikan pesan.")
    st.markdown("")

    with st.container(border=True):
        uploaded = st.file_uploader(
            "Upload Audio (WAV)",
            type=["wav"],
            key=f"validate_uploader_{st.session_state['uploader_version']}",
            help="Hanya menerima WAV PCM 16-bit tidak terkompresi",
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
                col_b.metric("Sample Rate", f"{info['framerate']} Hz")
                col_c.metric("Durasi", f"{info['duration_sec']} s")

                st.info(
                    f"💾 **Kapasitas payload:** {_fmt_capacity(info['capacity_payload'])} "
                    f"({info['capacity_payload']:,} byte)"
                )

                st.audio(audio_bytes, format="audio/wav")

                st.session_state["validated_audio_bytes"] = audio_bytes
                st.session_state["validated_audio_name"] = uploaded.name
                st.session_state["validated_audio_info"] = info

                st.success(
                    f"Audio **{uploaded.name}** tersimpan. "
                    f"Lanjut ke tab **📤 Kirim Pesan**."
                )

            else:
                st.error(f"❌ Audio tidak valid: {error_reason}")

                try:
                    sf_info = sf.info(io.BytesIO(audio_bytes))
                    st.caption(
                        f"Format aktual: **{sf_info.format} / {sf_info.subtype}** · "
                        f"{sf_info.samplerate} Hz · {sf_info.channels} ch"
                    )
                except Exception:
                    st.caption("Format aktual: tidak dikenali oleh soundfile.")

                st.markdown("#### 🛠️ Konversi ke PCM 16-bit")

                with st.spinner("Mencoba konversi otomatis..."):
                    try:
                        data, sr = sf.read(io.BytesIO(audio_bytes))
                        buf = io.BytesIO()
                        sf.write(buf, data, sr, format="WAV", subtype="PCM_16")
                        converted = buf.getvalue()
                        read_wav_bytes(converted)

                        st.success("✅ Konversi otomatis berhasil.")
                        st.audio(converted, format="audio/wav")

                        st.download_button(
                            label="⬇️ Unduh WAV PCM 16-bit",
                            data=converted,
                            file_name=f"pcm16_{uploaded.name}",
                            mime="audio/wav",
                            key="download_converted",
                        )
                        st.markdown(
                            '<p class="dl-hint">Unduh lalu upload ulang di atas untuk verifikasi.</p>',
                            unsafe_allow_html=True,
                        )
                        _notify_on_download("Unduh WAV PCM 16-bit")

                    except Exception as e:
                        st.warning(f"Konversi otomatis gagal: {e}")
                        st.write("Gunakan **ffmpeg** di terminal:")
                        out_name = Path(uploaded.name).stem + "_pcm16.wav"
                        st.code(
                            f'ffmpeg -i "{uploaded.name}" -c:a pcm_s16le -ar 48000 -ac 2 "{out_name}"',
                            language="bash",
                        )


# =====================================================================
# TAB 2 — KIRIM PESAN
# =====================================================================
with tab_kirim:
    st.markdown("### 📤 Kirim Pesan Rahasia")
    st.caption("Pesan akan dienkripsi AES-256-GCM lalu disisipkan ke bit LSB audio.")
    st.markdown("")

    validated_bytes = st.session_state.get("validated_audio_bytes")
    validated_name = st.session_state.get("validated_audio_name")

    audio_bytes = None
    source_name = None

    if validated_bytes is not None:
        with st.container(border=True):
            col_l, col_r = st.columns([3, 1])
            with col_l:
                st.success(f"✅ Audio tervalidasi: **{validated_name}**")
            with col_r:
                if st.button("🔄 Ganti", key="reset_audio", use_container_width=True):
                    st.session_state.pop("validated_audio_bytes", None)
                    st.session_state.pop("validated_audio_name", None)
                    st.session_state.pop("validated_audio_info", None)
                    st.session_state["uploader_version"] += 1
                    st.session_state["_auto_open_uploader"] = True
                    st.rerun()
            st.audio(validated_bytes, format="audio/wav")
        audio_bytes = validated_bytes
        source_name = validated_name
    else:
        st.info(
            "💡 Belum ada audio tervalidasi. Upload di bawah untuk langsung memakai, "
            "atau gunakan tab **🔍 Validasi** untuk diagnosa lebih lengkap."
        )

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        with st.container(border=True):
            st.markdown("##### 1. Audio Sumber")
            if audio_bytes is None:
                uploaded_kirim = st.file_uploader(
                    "Upload Audio (WAV PCM 16-bit)",
                    type=["wav"],
                    key=f"kirim_uploader_{st.session_state['uploader_version']}",
                )

                if st.session_state.get("_auto_open_uploader"):
                    st.session_state.pop("_auto_open_uploader", None)
                    _auto_open_uploader_in_tab()

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

        with st.container(border=True):
            st.markdown("##### 2. Pesan & Kunci")
            pesan = st.text_area(
                "Pesan Rahasia",
                placeholder="Ketik pesan yang ingin disembunyikan...",
                key="kirim_pesan",
                height=120,
            )
            passphrase = st.text_input(
                "Passphrase",
                type="password",
                key="kirim_key",
                placeholder="Kunci enkripsi (bebas)",
            )

            if audio_bytes is not None and pesan:
                samples_c, _ = read_wav_bytes(audio_bytes)
                cap = capacity_bytes(samples_c) - HEADER_SIZE
                pesan_len = len(pesan.encode("utf-8"))
                pct = pesan_len / cap * 100 if cap > 0 else 0
                if pesan_len > cap:
                    st.warning(
                        f"⚠️ Pesan ({pesan_len:,} B) melebihi kapasitas "
                        f"({_fmt_capacity(cap)})"
                    )
                else:
                    st.caption(
                        f"📏 Pesan: {pesan_len:,} B · Kapasitas: {_fmt_capacity(cap)} "
                        f"({pct:.1f}% terpakai)"
                    )

            btn_embed = st.button(
                "🔒 Sisipkan Pesan",
                type="primary",
                use_container_width=True,
                disabled=audio_bytes is None or not pesan or not passphrase,
            )

    with col2:
        with st.container(border=True):
            st.markdown("##### 3. Hasil")
            if btn_embed:
                with st.spinner("Memproses..."):
                    try:
                        stego_bytes, info = embed(
                            audio_bytes, pesan.encode(), passphrase
                        )
                        st.toast("✅ Audio stego siap diunduh!", icon="🎉")
                        st.success("🎉 Pesan berhasil disisipkan!")

                        st.markdown("**🔊 Audio Asli:**")
                        st.audio(audio_bytes, format="audio/wav")
                        st.markdown("**🎧 Audio Stego:**")
                        st.audio(stego_bytes, format="audio/wav")

                        st.download_button(
                            label="⬇️ Unduh Audio Stego",
                            data=stego_bytes,
                            file_name=f"STEGO_{source_name or 'audio.wav'}",
                            mime="audio/wav",
                            key="download_stego",
                            use_container_width=True,
                        )
                        _notify_on_download("Unduh Audio Stego")

                        st.markdown("---")
                        st.markdown("**📊 Metrik:**")
                        col_m1, col_m2 = st.columns(2)
                        col_m1.metric("SNR", f"{info['snr_db']:.2f} dB")
                        col_m2.metric("MSE", f"{info['mse']:.2e}")
                        with st.expander("Detail lengkap"):
                            st.json(info)
                    except Exception as e:
                        st.error(f"Gagal: {e}")
            else:
                st.caption("Hasil embed akan muncul di sini.")
                st.markdown(
                    '<div style="text-align: center; padding: 40px 0; opacity: 0.3; font-size: 3rem;">🎧</div>',
                    unsafe_allow_html=True,
                )


# =====================================================================
# TAB 3 — TERIMA PESAN
# =====================================================================
with tab_terima:
    st.markdown("### 📥 Terima & Ekstrak Pesan")
    st.caption("Upload audio stego, masukkan passphrase, sistem akan mengekstrak dan mendekripsi.")
    st.markdown("")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        with st.container(border=True):
            st.markdown("##### 1. Audio Stego")
            stego_file = st.file_uploader(
                "Upload Audio Stego",
                type=["wav"],
                key="terima_uploader",
            )
            passphrase_ext = st.text_input(
                "Passphrase",
                type="password",
                key="terima_key",
                placeholder="Kunci dekripsi",
            )
            btn_extract = st.button(
                "🔓 Ekstrak Pesan",
                type="primary",
                use_container_width=True,
                disabled=stego_file is None or not passphrase_ext,
            )

    with col2:
        with st.container(border=True):
            st.markdown("##### 2. Pesan Terbaca")
            if btn_extract:
                with st.spinner("Mengekstrak dan mendekripsi..."):
                    try:
                        stego_bytes = stego_file.read()
                        plaintext, info = extract(stego_bytes, passphrase_ext)
                        st.toast("✅ Pesan berhasil diekstrak!", icon="🎉")
                        st.success("🎉 Pesan berhasil diekstrak!")
                        st.text_area(
                            "Pesan Rahasia:",
                            value=plaintext.decode("utf-8", errors="replace"),
                            height=180,
                        )
                        with st.expander("Detail proses"):
                            st.json(info)
                    except InvalidTag:
                        st.error(
                            "❌ **Passphrase salah**, atau audio telah dimodifikasi/dirusak. "
                            "AES-GCM menolak mengembalikan data yang tidak valid."
                        )
                    except ValueError as e:
                        st.error(f"❌ Gagal: {e}")
                    except Exception as e:
                        st.error(f"❌ Error tidak terduga: {e}")
            else:
                st.caption("Pesan hasil dekripsi akan muncul di sini.")
                st.markdown(
                    '<div style="text-align: center; padding: 40px 0; opacity: 0.3; font-size: 3rem;">🔐</div>',
                    unsafe_allow_html=True,
                )


# =====================================================================
# TAB 4 — HASIL UJI
# =====================================================================
with tab_uji:
    st.markdown("### 📊 Hasil Pengujian")
    st.caption("Benchmark 10 payload dan robustness test pada audio uji `Married_Life.wav`.")
    st.markdown("")

    csv_path = Path("output/benchmark_results.csv")
    img_path = Path("output/benchmark_charts.png")

    with st.container(border=True):
        st.markdown("#### 🎯 Benchmark — 10 Payload")
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            st.dataframe(
                df[["size_label", "snr_db", "mse",
                    "embed_total_ms", "extract_total_ms", "status"]],
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "SNR turun secara logaritmik seiring payload membesar, "
                "namun tetap di atas 60 dB → **kualitas audio praktis tidak berubah**."
            )
        else:
            st.warning("Belum ada CSV. Jalankan `python -m src.benchmark`.")

        if img_path.exists():
            st.image(str(img_path), caption="Grafik benchmark 2×2", use_container_width=True)
        else:
            st.warning("Belum ada grafik. Jalankan `python -m src.benchmark`.")

    st.markdown("")

    with st.container(border=True):
        st.markdown("#### 🛡️ Robustness Test")
        robust_path = Path("output/robustness_results.csv")
        if robust_path.exists():
            df_r = pd.read_csv(robust_path)
            st.dataframe(df_r, use_container_width=True, hide_index=True)
            st.caption(
                "Baris **GAGAL (Aman)** membuktikan sistem mendeteksi manipulasi "
                "audio dan menolak menyerahkan data rusak — bukti *authenticated encryption* bekerja."
            )
        else:
            st.info("Belum ada data robustness. Jalankan `python -m src.robustness`.")