import sys
from pathlib import Path

# Tambahkan root project ke sys.path agar import src.* bekerja
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st
from cryptography.exceptions import InvalidTag

from src.pipeline import embed, extract

# Konfigurasi Halaman
st.set_page_config(page_title="Sonicrypt", page_icon="🎵", layout="wide")

st.title("🎵 Sonicrypt")
st.caption("Audio Dead-Drop — AES-GCM + LSB pada Audio WAV")
st.markdown("---")

# Buat 3 Tab
tab_kirim, tab_terima, tab_uji = st.tabs(["📤 Kirim Pesan", "📥 Terima Pesan", "📊 Hasil Uji"])

# ==========================================
# TAB 1: KIRIM PESAN
# ==========================================
with tab_kirim:
    st.header("Sembunyikan Pesan dalam Audio")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        audio_file = st.file_uploader("Upload Audio (WAV PCM 16-bit)", type=["wav"])
        pesan = st.text_area("Pesan Rahasia", placeholder="Ketik pesan yang ingin disembunyikan...")
        passphrase = st.text_input("Passphrase", type="password", placeholder="Kunci enkripsi...")
        btn_embed = st.button("🔒 Sisipkan & Unduh Audio", type="primary", use_container_width=True)
        
    with col2:
        if btn_embed:
            if not audio_file or not pesan or not passphrase:
                st.error("Audio, pesan, dan passphrase wajib diisi!")
            else:
                with st.spinner("Memproses..."):
                    try:
                        # Baca bytes dari uploader
                        audio_bytes = audio_file.read()
                        
                        # Jalankan pipeline
                        stego_bytes, info = embed(audio_bytes, pesan.encode(), passphrase)
                        
                        st.success("Pesan berhasil disisipkan!")
                        
                        # Player audio asli vs stego
                        st.write("**Audio Asli:**")
                        st.audio(audio_bytes, format="audio/wav")
                        
                        st.write("**Audio Stego (Hasil):**")
                        st.audio(stego_bytes, format="audio/wav")
                        
                        # Tombol download
                        st.download_button(
                            label="⬇️ Unduh Audio Stego",
                            data=stego_bytes,
                            file_name=f"stego_{audio_file.name}",
                            mime="audio/wav",
                            use_container_width=True
                        )
                        
                        # Tampilkan metrik
                        st.json(info)
                        
                    except Exception as e:
                        st.error(f"Gagal: {e}")

# ==========================================
# TAB 2: TERIMA PESAN
# ==========================================
with tab_terima:
    st.header("Ekstrak Pesan dari Audio")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        stego_file = st.file_uploader("Upload Audio Stego", type=["wav"])
        passphrase_ext = st.text_input("Passphrase", type="password", key="ext_key", placeholder="Kunci dekripsi...")
        btn_extract = st.button("🔓 Ekstrak Pesan", type="primary", use_container_width=True)
        
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
                        st.text_area("Pesan Rahasia:", value=plaintext.decode('utf-8', errors='replace'), height=150)
                        st.json(info)
                        
                    except InvalidTag:
                        st.error("❌ Gagal: Passphrase salah, atau audio telah dimodifikasi/dirusak.")
                    except ValueError as e:
                        st.error(f"❌ Gagal: {e}")
                    except Exception as e:
                        st.error(f"❌ Error tidak terduga: {e}")

# ==========================================
# TAB 3: HASIL UJI
# ==========================================
with tab_uji:
    st.header("Benchmark: 10 Payload pada Audio Asli")
    st.write("Data ini di-generate dari script `python -m src.benchmark` pada `married_life.wav`.")
    
    csv_path = Path("output/benchmark_results.csv")
    img_path = Path("output/benchmark_charts.png")
    
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        st.dataframe(
            df[["size_label", "snr_db", "mse", "embed_total_ms", "extract_total_ms", "status"]],
            use_container_width=True
        )
    else:
        st.warning("File CSV belum ada. Jalankan `python -m src.benchmark` terlebih dahulu.")

    if img_path.exists():
        st.image(str(img_path), caption="Grafik Benchmark", use_container_width=True)
    else:
        st.warning("File grafik belum ada. Jalankan `python -m src.benchmark` terlebih dahulu.")