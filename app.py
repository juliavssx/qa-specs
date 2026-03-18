import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuração da Página ---
st.set_page_config(page_title="QA Hub - Smart Specs", layout="wide")

# Estilo para remover espaços desnecessários
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    [data-testid="stMetricValue"] { font-size: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

SAFE_AREAS = {
    "Adstream/TV (Manual)": {"file": "Adstream_1920x1080.png", "width": 1920, "height": 1080},
    "YouTube Horizontal": {"file": "YTHorizontal.svg", "width": 1920, "height": 1080},
    "YouTube Shorts": {"file": "YT_Shorts_1080x1920.png", "width": 1080, "height": 1920},
    "Meta Reel": {"file": "Meta_Reel_1080x1920.png", "width": 1080, "height": 1920},
    "Meta Stories": {"file": "Meta_Stories_1080x1920.png", "width": 1080, "height": 1920},
    "TikTok": {"file": "Tiktok_Topview_e_Infeed Ads_540x960.png", "width": 540, "height": 960},
    "Pinterest": {"file": "Pinterest_1080x1920.png", "width": 1080, "height": 1920}
}

def validate_dimensions(img, target_w, target_h):
    actual_ratio = img.width / img.height
    target_ratio = target_w / target_h
    return abs(actual_ratio - target_ratio) < 0.03

def apply_safe_area(img_orig, config, opacity):
    real_w, real_h = img_orig.size
    overlay_filename = config["file"]
    if overlay_filename and os.path.exists(overlay_filename):
        try:
            overlay = Image.open(overlay_filename).convert("RGBA")
            overlay = overlay.resize((real_w, real_h), Image.Resampling.LANCZOS)
            alpha = overlay.getchannel('A')
            new_alpha = alpha.point(lambda i: i * opacity)
            overlay.putalpha(new_alpha)
            return Image.alpha_composite(img_orig, overlay)
        except: return img_orig
    return img_orig

# --- Interface Sidebar ---
with st.sidebar:
    st.title("🛠️ Smart QA Toolbox")
    ferramenta = st.radio("Selecione a Ferramenta:", ["Scanner & Safe Areas", "Comparador (V1 vs V2)"])
    st.markdown("---")
    
    if ferramenta == "Scanner & Safe Areas":
        arquivo = st.file_uploader("Upload do Asset:", type=["png", "jpg", "jpeg"])
        modo = st.selectbox("Plataforma / Destino:", list(SAFE_AREAS.keys()))
        opacidade = st.slider("Opacidade da Safe Area:", 0.0, 1.0, 0.70)
    else:
        v1_file = st.file_uploader("Versão 1 (Original):", type=["png", "jpg", "jpeg"], key="v1")
        v2_file = st.file_uploader("Versão 2 (Alterada):", type=["png", "jpg", "jpeg"], key="v2")

# --- Área Principal ---
if ferramenta == "Scanner & Safe Areas" and arquivo:
    config = SAFE_AREAS[modo]
    img_orig = Image.open(arquivo).convert("RGBA")
    
    if not validate_dimensions(img_orig, config["width"], config["height"]):
        st.error(f"⚠️ **Formato Incorreto!** Esperado: {config['width']}x{config['height']}.")
    else:
        # Processamento
        img_with_safe = apply_safe_area(img_orig, config, opacidade)
        
        # Criação das Colunas (Imagem | Espaço | Specs)
        col_img, col_spacer, col_specs = st.columns([1.5, 0.1, 0.6])
        
        with col_img:
            # Container escuro para a imagem
            st.image(img_with_safe, use_container_width=True)
            st.success("✅ Specs validadas.")

        with col_specs:
            st.markdown("### 📊 Informações Técnicas")
            
            # Formatação de Peso
            peso_val = arquivo.size/1024/1024
            peso_str = f"{peso_val:.2f} MB" if peso_val > 1 else f"{arquivo.size/1024:.0f} KB"
            
            # Cards de Informação
            st.metric("Formato", arquivo.name.split('.')[-1].upper())
            st.metric("Peso do Arquivo", peso_str)
            st.metric("Dimensões Reais", f"{img_orig.width} x {img_orig.height}")
            
            st.info(f"Veículo Selecionado:\n**{modo}**")

elif ferramenta == "Comparador (V1 vs V2)" and v1_file and v2_file:
    col1, col2 = st.columns(2)
    with col1: st.image(v1_file, caption="Versão 1", use_container_width=True)
    with col2: st.image(v2_file, caption="Versão 2", use_container_width=True)