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
    "YouTube Horizontal": {"file": "YTHorizontal.png", "width": 1920, "height": 1080},  # ✅ Ajustado para .png
    "YouTube Shorts": {"file": "YT_Shorts_1080x1920.png", "width": 1080, "height": 1920},
    "Meta Reel": {"file": "Meta_Reel_1080x1920.png", "width": 1080, "height": 1920},
    "Meta Stories": {"file": "Meta_Stories_1080x1920.png", "width": 1080, "height": 1920},
    "TikTok": {"file": "Tiktok_Topview_e_Infeed Ads_540x960.png", "width": 540, "height": 960},
    "Pinterest": {"file": "Pinterest_1080x1920.png", "width": 1080, "height": 1920}
}

# Limite máximo de upload total (em MB)
MAX_UPLOAD_SIZE_MB = 500
MAX_FILES = 10

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

def validate_total_size(files):
    total_bytes = sum([get_file_size_bytes(f) for f in files])
    total_mb = total_bytes / (1024 * 1024)
    if total_mb > MAX_UPLOAD_SIZE_MB:
        st.error(f"❌ Tamanho total excede o limite de {MAX_UPLOAD_SIZE_MB}MB")
        return False
    return True

def analyze_video(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp.write(uploaded_file.read())
        video_path = tmp.name
    cap = cv2.VideoCapture(video_path)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = round(cap.get(cap.get(cv2.CAP_PROP_FPS)), 2)
    cap.release()
    os.unlink(video_path)
    uploaded_file.seek(0)
    return width, height, fps

def apply_safe_area(img_orig, config, opacity):
    real_w, real_h = img_orig.size
    overlay_filename = config.get("file")
    if not overlay_filename:
        return img_orig
    
    possible_paths = [overlay_filename, f"assets/{overlay_filename}", f"safe_areas/{overlay_filename}"]
    for path in possible_paths:
        if os.path.exists(path):
            overlay = Image.open(path).convert("RGBA")
            overlay = overlay.resize((real_w, real_h), Image.Resampling.LANCZOS)
            alpha = overlay.getchannel('A')
            new_alpha = alpha.point(lambda i: i * opacity)
            overlay.putalpha(new_alpha)
            return Image.alpha_composite(img_orig.convert("RGBA"), overlay)
    
    st.caption("ℹ️ Safe area não encontrada")
    return img_orig

def clean_size_format(raw_meta):
    if not raw_meta: return "⚠️ N/A"
    return raw_meta.lower().replace("width=", "").replace("height=", "").replace(" ", "").replace(",", "x")

def validate_html5_package(zip_file):
    report = {"html_found": False, "click_tag": False, "size_meta": None, "kb_size": zip_file.size / 1024, "files_list": []}
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            all_files = z.namelist()
            report["files_list"] = [f for f in all_files if not f.startswith('__MACOSX')]
            html_files = [f for f in all_files if f.lower().endswith('.html') and not "__MACOSX" in f]
            if html_files:
                report["html_found"] = True
                with z.open(html_files[0]) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(content, 'html.parser')
                    size_tag = soup.find('meta', attrs={'name': 'ad.size'})
                    if size_tag: 
                        report["size_meta"] = clean_size_format(size_tag.get('content'))
                    report["click_tag"] = "clickTag" in content or "clicktag" in content.lower()
    except Exception as e:
        st.warning(f"Erro no ZIP: {str(e)}")
    zip_file.seek(0)
    return report

def process_file(arquivo, modo, opacidade):
    ext = arquivo.name.split('.')[-1].lower()
    config = SAFE_AREAS[modo]
    resultado = {"nome": arquivo.name, "tipo": ext, "tamanho": get_file_size_bytes(arquivo), "detalhes": {}}
    
    if ext == "zip":
        resultado["detalhes"] = validate_html5_package(arquivo)
    elif ext in ["mp4", "mov"]:
        try:
            w, h, fps = analyze_video(arquivo)
            resultado["detalhes"] = {"resolucao": f"{w}x{h}", "fps": fps, "fps_ok": abs(fps - 30) < 0.5}
        except: resultado["erro"] = "Erro ao ler vídeo"
    elif ext in ["png", "jpg", "jpeg"]:
        try:
            img = Image.open(arquivo)
            resultado["detalhes"] = {"dimensoes": f"{img.width}x{img.height}", "img_obj": img, "config": config, "opacidade": opacidade}
        except: resultado["erro"] = "Erro ao ler imagem"
    return resultado

def display_file_result(resultado, modo):
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"**📄 {resultado['nome']}**")
            st.caption(f"Tamanho: {get_file_size_formatted(resultado['tamanho'])}")
        with col2:
            if "erro" in resultado:
                st.error(resultado["erro"])
            elif resultado['tipo'] == "zip":
                res = resultado["detalhes"]
                st.success("✅ HTML5 Detectado")
                st.metric("ClickTag", "OK" if res["click_tag"] else "AUSENTE")
            elif resultado['tipo'] in ["mp4", "mov"]:
                st.metric("Resolução", resultado["detalhes"]["resolucao"])
            elif resultado['tipo'] in ["png", "jpg", "jpeg"]:
                img_safe = apply_safe_area(resultado["detalhes"]["img_obj"], resultado["detalhes"]["config"], resultado["detalhes"]["opacidade"])
                st.image(img_safe, use_container_width=True)

# --- Sidebar ---
with st.sidebar:
    st.title("🛠️ Smart QA Toolbox")
    ferramenta = st.radio("Selecione:", ["Scanner & Safe Areas", "Comparador"])
    
    if ferramenta == "Scanner & Safe Areas":
        arquivos = st.file_uploader("Assets:", type=["png", "jpg", "jpeg", "mp4", "mov", "zip"], accept_multiple_files=True)
        modo = st.selectbox("Plataforma:", list(SAFE_AREAS.keys()))
        opacidade = st.slider("Opacidade:", 0.0, 1.0, 0.70)
    else:
        v1 = st.file_uploader("V1:", type=["png", "jpg", "jpeg"])
        v2 = st.file_uploader("V2:", type=["png", "jpg", "jpeg"])

# --- Área Principal ---
st.markdown("# 🎯 QA Hub - Smart Specs")
st.markdown("---")

if ferramenta == "Scanner & Safe Areas":
    if not arquivos:
        st.info("👈 **Selecione os arquivos na barra lateral para começar**")
        
        # ✅ AJUSTADO: Alinhamento corrigido para evitar IndentationError
        with st.expander("📋 Como usar"):
            st.markdown("""
            ### Instruções de uso:
            1. Selecione os arquivos desejados (múltiplos permitidos)
            2. Escolha a plataforma de destino
            3. Ajuste a opacidade da safe area (para imagens)
            4. Analise os resultados para cada arquivo
            
            ### Formatos suportados:
            - **Imagens:** PNG, JPG, JPEG
            - **Vídeos:** MP4, MOV
            - **Pacotes HTML5:** ZIP
            """)
    else:
        progress_bar = st.progress(0)
        for i, arquivo in enumerate(arquivos):
            resultado = process_file(arquivo, modo, opacidade)
            display_file_result(resultado, modo)
            progress_bar.progress((i + 1) / len(arquivos))
        
        if st.button("🗑️ Limpar todos", type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

elif ferramenta == "Comparador":
    if v1 and v2:
        c1, c2 = st.columns(2)
        c1.image(v1, caption="Versão 1")
        c2.image(v2, caption="Versão 2")