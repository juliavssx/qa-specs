import streamlit as st
import base64
import os
import zipfile
import re
from PIL import Image
from pymediainfo import MediaInfo 
import tempfile

# 1. Configuração da Página
st.set_page_config(page_title="QA Hub Smart Scanner", layout="wide", page_icon="🎯")

# --- FUNÇÕES DE SUPORTE ---

def analisar_video_completo(uploaded_file):
    """Extrai metadados de vídeo para a barra de status e validação Adstream"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    media_info = MediaInfo.parse(tmp_path)
    v = next((t for t in media_info.tracks if t.track_type == "Video"), None)
    a = next((t for t in media_info.tracks if t.track_type == "Audio"), None)
    
    info = {
        "dimensao": f"{v.width}x{v.height}" if v else "N/A",
        "formato": uploaded_file.name.split('.')[-1].upper(),
        "peso": f"{uploaded_file.size / (1024*1024):.2f} MB",
        "v_track": v,
        "a_track": a
    }
    os.remove(tmp_path)
    return info

def get_local_img_b64(file_name):
    for ext in [".svg", ".SVG", ".png", ".jpg"]:
        path = f"{file_name}{ext}"
        if os.path.exists(path):
            with open(path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode()
                mime = "image/svg+xml" if "svg" in ext.lower() else "image/png"
                return b64_data, mime
    return None, None

# 2. Estilização CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #0e0e12; color: white; }
    .info-bar-container {
        background-color: #ffffff; color: #000000; padding: 10px 20px;
        border-radius: 0 0 12px 12px; display: flex; justify-content: space-between;
        align-items: center; margin-top: -5px; border: 1px solid #ddd;
        font-weight: 600; font-size: 13px; text-transform: uppercase;
    }
    .status-card { background: #1c1c24; padding: 15px; border-radius: 12px; border: 1px solid #2d2d3a; margin-bottom: 10px; }
    .metric-label { font-size: 10px; color: #888; text-transform: uppercase; }
    .metric-value { font-size: 16px; font-weight: 600; color: #00ffcc; }
</style>
""", unsafe_allow_html=True)

def render_info_bar(formato, peso, dimensao):
    st.markdown(f"""
        <div class="info-bar-container">
            <span>FORMATO: {formato}</span>
            <span>PESO: {peso}</span>
            <span>DIMENSÃO: {dimensao}</span>
        </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛠️ Smart QA Toolbox")
    modo = st.radio("Selecione a Ferramenta:", ["Scanner & Safe Areas", "Comparador (V1 vs V2)"])
    st.markdown("---")git add app.py

# --- MODO 1: SCANNER ---
if modo == "Scanner & Safe Areas":
    plataforma = st.sidebar.selectbox("Plataforma / Destino:", 
                                     ["YouTube (Automático)", "Adstream/TV (Manual)", "Meta (Manual)", "TikTok"])
    upload = st.sidebar.file_uploader("Upload do Asset", type=["png", "jpg", "mp4", "mov", "zip"], key="main_up")
    
    if upload:
        ext = upload.name.split('.')[-1].lower()
        
        # Lógica de Captura de Dados
        if ext in ['mp4', 'mov']:
            data = analisar_video_completo(upload)
            dim, format_name, peso_str = data['dimensao'], data['formato'], data['peso']
        else:
            img = Image.open(upload)
            dim, format_name, peso_str = f"{img.size[0]}x{img.size[1]}", ext.upper(), f"{upload.size/(1024*1024):.2f} MB"

        # Lógica de Safe Areas
        safe_key = "Adstream_1920x1080" if plataforma == "Adstream/TV (Manual)" else "YTHorizontal"
        label_display = plataforma

        col_v, col_s = st.columns([1.6, 1])
        with col_v:
            if ext in ['mp4', 'mov']: st.video(upload)
            else: st.image(upload, use_container_width=True)
            
            render_info_bar(format_name, peso_str, dim) # Barra Branca Universal

            if plataforma == "Adstream/TV (Manual)" and ext in ['mp4', 'mov']:
                st.markdown("### 🔍 Relatório de Specs (PDF Adstream)")
                v, a = data['v_track'], data['a_track']
                if v and a:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.info(f"FPS 29.97: {'✅' if float(v.frame_rate) == 29.97 else '❌'} ({v.frame_rate})")
                        st.info(f"Scan: {'✅' if v.scan_type == 'Interlaced' else '❌'} ({v.scan_type})")
                    with c2:
                        st.info(f"Audio 24bit: {'✅' if a.bit_depth == 24 else '❌'}")
                        st.info(f"Sample 48kHz: {'✅' if int(a.sampling_rate) == 48000 else '❌'}")

# --- MODO 2: COMPARADOR ---
elif modo == "Comparador (V1 vs V2)":
    st.subheader("↔️ Comparador de Versões")
    v1 = st.sidebar.file_uploader("V1", type=["png", "jpg", "mp4", "mov"], key="v1")
    v2 = st.sidebar.file_uploader("V2", type=["png", "jpg", "mp4", "mov"], key="v2")
    c1, c2 = st.columns(2)
    for i, file in enumerate([v1, v2]):
        if file:
            with (c1 if i==0 else c2):
                if file.name.lower().endswith(('mp4', 'mov')):
                    st.video(file)
                    d = analisar_video_completo(file)
                    render_info_bar(d['formato'], d['peso'], d['dimensao'])
                else:
                    st.image(file)
                    img = Image.open(file)
                    render_info_bar(file.name.split('.')[-1].upper(), f"{file.size/(1024*1024):.2f} MB", f"{img.size[0]}x{img.size[1]}")
