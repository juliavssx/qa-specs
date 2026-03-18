import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import cv2
import tempfile
import os
import zipfile
from bs4 import BeautifulSoup

# --- Configuração da Página ---
st.set_page_config(page_title="QA Hub - Smart Specs", layout="wide")

SAFE_AREAS = {
    "Adstream/TV (Manual)": {"file": "Adstream_1920x1080.png", "width": 1920, "height": 1080},
    "Google/DCM (HTML5)": {"file": None, "width": None, "height": None},
    "YouTube Horizontal": {"file": "YTHorizontal.svg", "width": 1920, "height": 1080},
    "YouTube Shorts": {"file": "YT_Shorts_1080x1920.png", "width": 1080, "height": 1920},
    "Meta Reel": {"file": "Meta_Reel_1080x1920.png", "width": 1080, "height": 1920},
    "Meta Stories": {"file": "Meta_Stories_1080x1920.png", "width": 1080, "height": 1920},
    "TikTok": {"file": "Tiktok_Topview_e_Infeed Ads_540x960.png", "width": 540, "height": 960},
    "Pinterest": {"file": "Pinterest_1080x1920.png", "width": 1080, "height": 1920}
}

# --- Funções de Suporte ---
def get_file_size(file):
    """Retorna o peso do arquivo formatado"""
    size_bytes = file.size
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
    return width, height, fps

def apply_safe_area(img_orig, config, opacity):
    real_w, real_h = img_orig.size
    overlay_filename = config.get("file")
    if overlay_filename and os.path.exists(overlay_filename):
        overlay = Image.open(overlay_filename).convert("RGBA")
        overlay = overlay.resize((real_w, real_h), Image.Resampling.LANCZOS)
        alpha = overlay.getchannel('A')
        new_alpha = alpha.point(lambda i: i * opacity)
        overlay.putalpha(new_alpha)
        return Image.alpha_composite(img_orig, overlay)
    return img_orig

def clean_size_format(raw_meta):
    if not raw_meta: return "⚠️ N/A"
    clean = raw_meta.lower().replace("width=", "").replace("height=", "").replace(" ", "").replace(",", "x")
    return clean

def validate_html5_package(zip_file):
    report = {
        "html_found": False, "click_tag": False, "size_meta": None, 
        "file_path": "", "raw_html": "", "type": "Desconhecido", "kb_size": zip_file.size / 1024
    }
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            all_files = z.namelist()
            html_files = [f for f in all_files if f.lower().endswith('.html') and not "__MACOSX" in f]
            if html_files:
                target_path = html_files[0]
                report["html_found"] = True
                report["file_path"] = target_path
                with z.open(target_path) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    report["raw_html"] = content
                    soup = BeautifulSoup(content, 'html.parser')
                    size_tag = soup.find('meta', attrs={'name': 'ad.size'})
                    if size_tag: 
                        report["size_meta"] = clean_size_format(size_tag.get('content'))
                        report["type"] = "Google DCM"
                    if "EBG" in content or "EBModulesHelper" in content:
                        report["type"] = "Sizmek / Portal"
                    elif report["type"] == "Desconhecido" and ("clickTag" in content or "clicktag" in content.lower()):
                        report["type"] = "Portal (Nacional)"
                    if "clickTag" in content or "clicktag" in content.lower():
                        report["click_tag"] = True
    except: pass
    return report

# --- Sidebar ---
with st.sidebar:
    st.title("🛠️ Smart QA Toolbox")
    ferramenta = st.radio("Selecione a Ferramenta:", ["Scanner & Safe Areas", "Comparador (V1 vs V2)"])
    
    if ferramenta == "Scanner & Safe Areas":
        arquivo = st.file_uploader("Upload do Asset:", type=["png", "jpg", "jpeg", "mp4", "mov", "zip"])
        modo = st.selectbox("Plataforma / Destino:", list(SAFE_AREAS.keys()))
        if arquivo and arquivo.name.split('.')[-1].lower() in ["png", "jpg", "jpeg"]:
            opacidade = st.slider("Opacidade da Safe Area:", 0.0, 1.0, 0.70)
    else:
        v1 = st.file_uploader("Versão 1 (Antiga):", type=["png", "jpg", "jpeg"])
        v2 = st.file_uploader("Versão 2 (Nova):", type=["png", "jpg", "jpeg"])

# --- Área Principal ---
if ferramenta == "Scanner & Safe Areas" and arquivo:
    ext = arquivo.name.split('.')[-1].lower()
    config = SAFE_AREAS[modo]
    col_asset, col_spacer, col_specs = st.columns([1.5, 0.1, 0.6])

    # 🌐 FLUXO HTML5 (.ZIP)
    if ext == "zip":
        report = validate_html5_package(arquivo)
        with col_asset:
            st.info(f"📦 Pacote Detectado: {arquivo.name}")
            if report["html_found"]:
                st.success(f"Tipo: **{report['type']}**")
                components.html(report["raw_html"], height=500, scrolling=True)
            else:
                st.error("❌ Erro: Nenhum arquivo .html encontrado no ZIP.")
        with col_specs:
            st.markdown(f"### 🌐 {report['type']} Specs")
            peso_ok = report["kb_size"] <= 150
            st.metric("Peso do ZIP", f"{report['kb_size']:.1f} KB", 
                      delta="✅ OK" if peso_ok else "❌ PESADO", 
                      delta_color="normal" if peso_ok else "inverse")
            if not peso_ok: st.warning("⚠️ Limite de 150KB excedido!")
            st.metric("Formato", report["size_meta"])
            st.metric("ClickTag", "✅ OK" if report["click_tag"] else "❌ AUSENTE")

    # 📽️ FLUXO VÍDEO (.MP4 / .MOV)
    elif ext in ["mp4", "mov"]:
        v_w, v_h, v_fps = analyze_video(arquivo)
        with col_asset: st.video(arquivo)
        with col_specs:
            st.markdown("### 📽️ Vídeo Specs")
            st.metric("Peso", get_file_size(arquivo))
            st.metric("Resolução", f"{v_w}x{v_h}")
            st.metric("FPS", f"{v_fps}", delta="✅ OK" if abs(v_fps-29.97)<0.1 else "❌ Erro")
            if modo == "Adstream/TV (Manual)":
                st.info("**Adstream Checklist:**\n- Loudness: -23/-24 LUFS\n- Timeline: Claquete(5s)+Black(2s)")

    # 📊 FLUXO IMAGEM (JPG / PNG)
    else:
        img_orig = Image.open(arquivo).convert("RGBA")
        img_with_safe = apply_safe_area(img_orig, config, opacidade)
        with col_asset: st.image(img_with_safe, use_container_width=True)
        with col_specs:
            st.markdown("### 📊 Imagem Specs")
            st.metric("Peso", get_file_size(arquivo))
            st.metric("Dimensões", f"{img_orig.width}x{img_orig.height}")

# 2. COMPARADOR
elif ferramenta == "Comparador (V1 vs V2)" and v1 and v2:
    c1, c2 = st.columns(2)
    with c1: st.image(v1, caption=f"V1 - {get_file_size(v1)}", use_container_width=True)
    with c2: st.image(v2, caption=f"V2 - {get_file_size(v2)}", use_container_width=True)