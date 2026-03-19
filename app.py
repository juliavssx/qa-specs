import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import cv2
import tempfile
import os
import zipfile
from bs4 import BeautifulSoup
import time

# --- Configuração da Página ---
st.set_page_config(
    page_title="QA Hub - Smart Specs", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constantes ---
SAFE_AREAS = {
    "Adstream/TV (Manual)": {"file": "Adstream_1920x1080.png", "width": 1920, "height": 1080},
    "Google/DCM (HTML5)": {"file": None, "width": None, "height": None},
    "YouTube Horizontal": {"file": "YTHorizontal.png", "width": 1920, "height": 1080},
    "YouTube Shorts": {"file": "YT_Shorts_1080x1920.png", "width": 1080, "height": 1920},
    "Meta Reel": {"file": "Meta_Reel_1080x1920.png", "width": 1080, "height": 1920},
    "Meta Stories": {"file": "Meta_Stories_1080x1920.png", "width": 1080, "height": 1920},
    "TikTok": {"file": "Tiktok_Topview_e_Infeed Ads_540x960.png", "width": 540, "height": 960},
    "Pinterest": {"file": "Pinterest_1080x1920.png", "width": 1080, "height": 1920}
}

MAX_UPLOAD_SIZE_MB = 500

# --- Funções de Suporte ---
def get_file_size_bytes(file):
    if hasattr(file, 'size'):
        return file.size
    return 0

def get_file_size_formatted(size_bytes):
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def analyze_video(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp.write(uploaded_file.read())
        video_path = tmp.name
    cap = cv2.VideoCapture(video_path)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = round(cap.get(cv2.CAP_PROP_FPS), 2)
    cap.release()
    os.unlink(video_path)
    uploaded_file.seek(0)
    return width, height, fps

def apply_safe_area(img_orig, config, opacity):
    real_w, real_h = img_orig.size
    overlay_filename = config.get("file")
    if not overlay_filename:
        return img_orig
    
    # Busca o arquivo de safe area em pastas comuns
    possible_paths = [overlay_filename, f"assets/{overlay_filename}", f"safe_areas/{overlay_filename}"]
    for path in possible_paths:
        if os.path.exists(path):
            overlay = Image.open(path).convert("RGBA")
            overlay = overlay.resize((real_w, real_h), Image.Resampling.LANCZOS)
            alpha = overlay.getchannel('A')
            new_alpha = alpha.point(lambda i: i * opacity)
            overlay.putalpha(new_alpha)
            return Image.alpha_composite(img_orig.convert("RGBA"), overlay)
    
    return img_orig

def validate_html5_package(zip_file):
    report = {"html_found": False, "click_tag": False, "size_meta": None, "kb_size": zip_file.size / 1024}
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            html_files = [f for f in z.namelist() if f.lower().endswith('.html') and not "__MACOSX" in f]
            if html_files:
                report["html_found"] = True
                with z.open(html_files[0]) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    report["click_tag"] = "clickTag" in content or "clicktag" in content.lower()
    except: pass
    zip_file.seek(0)
    return report

def process_file(arquivo, modo, opacidade):
    ext = arquivo.name.split('.')[-1].lower()
    config = SAFE_AREAS[modo]
    resultado = {"nome": arquivo.name, "tipo": ext, "tamanho": get_file_size_bytes(arquivo), "detalhes": {}}
    
    if ext == "zip":
        resultado["detalhes"] = validate_html5_package(arquivo)
    elif ext in ["mp4", "mov"]:
        w, h, fps = analyze_video(arquivo)
        resultado["detalhes"] = {"resolucao": f"{w}x{h}", "fps": fps}
    elif ext in ["png", "jpg", "jpeg"]:
        img = Image.open(arquivo)
        resultado["detalhes"] = {"dimensoes": f"{img.width}x{img.height}", "img_obj": img, "config": config, "opacidade": opacidade}
    return resultado

def display_file_result(resultado, modo):
    with st.container():
        st.markdown(f"### 📄 {resultado['nome']}")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write(f"**Tamanho:** {get_file_size_formatted(resultado['tamanho'])}")
            if resultado['tipo'] == "zip":
                st.write(f"**ClickTag:** {'✅ OK' if resultado['detalhes']['click_tag'] else '❌ Ausente'}")
            elif resultado['tipo'] in ["mp4", "mov"]:
                st.write(f"**Resolução:** {resultado['detalhes']['resolucao']}")
                st.write(f"**FPS:** {resultado['detalhes']['fps']}")
            elif resultado['tipo'] in ["png", "jpg", "jpeg"]:
                st.write(f"**Dimensões:** {resultado['detalhes']['dimensoes']}")
        
        with col2:
            if resultado['tipo'] in ["png", "jpg", "jpeg"]:
                img_safe = apply_safe_area(resultado["detalhes"]["img_obj"], resultado["detalhes"]["config"], resultado["detalhes"]["opacidade"])
                # FIX AQUI: use_column_width para compatibilidade
                st.image(img_safe, use_column_width=True)

# --- Sidebar ---
with st.sidebar:
    st.title("🛠️ Smart QA Toolbox")
    ferramenta = st.radio("Selecione:", ["Scanner & Safe Areas", "Comparador"])
    
    if ferramenta == "Scanner & Safe Areas":
        arquivos = st.file_uploader("Assets:", type=["png", "jpg", "jpeg", "mp4", "mov", "zip"], accept_multiple_files=True)
        modo = st.selectbox("Plataforma:", list(SAFE_AREAS.keys()))
        opacidade = st.slider("Opacidade Safe Area:", 0.0, 1.0, 0.70)
    else:
        v1 = st.file_uploader("V1:", type=["png", "jpg", "jpeg"])
        v2 = st.file_uploader("V2:", type=["png", "jpg", "jpeg"])

# --- Área Principal ---
st.markdown("# 🎯 QA Hub - Smart Specs")
st.markdown("---")

if ferramenta == "Scanner & Safe Areas":
    if not arquivos:
        st.info("👈 **Selecione os arquivos na barra lateral para começar**")
    else:
        for arquivo in arquivos:
            res = process_file(arquivo, modo, opacidade)
            display_file_result(res, modo)
            st.markdown("---")

elif ferramenta == "Comparador":
    if v1 and v2:
        c1, c2 = st.columns(2)
        with c1:
            st.image(v1, caption="Versão 1", use_column_width=True)
        with c2:
            st.image(v2, caption="Versão 2", use_column_width=True)