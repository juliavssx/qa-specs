import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuração da Página ---
st.set_page_config(page_title="QA Hub - Smart Specs", layout="wide")

# Dicionário de Configurações das Safe Areas
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
    """Verifica se a proporção da imagem é compatível"""
    actual_ratio = img.width / img.height
    target_ratio = target_w / target_h
    return abs(actual_ratio - target_ratio) < 0.03

def process_qa_view(image_file, config, modo_nome, opacity):
    img_orig = Image.open(image_file).convert("RGBA")
    real_w, real_h = img_orig.size
    
    # Barreira de Segurança
    if not validate_dimensions(img_orig, config["width"], config["height"]):
        st.error(f"⚠️ **Formato Incorreto!** Esperado: {config['width']}x{config['height']}.")
        return None

    # Aplica Safe Area com Opacidade
    overlay_filename = config["file"]
    if overlay_filename and os.path.exists(overlay_filename):
        try:
            overlay = Image.open(overlay_filename).convert("RGBA")
            overlay = overlay.resize((real_w, real_h), Image.Resampling.LANCZOS)
            alpha = overlay.getchannel('A')
            new_alpha = alpha.point(lambda i: i * opacity)
            overlay.putalpha(new_alpha)
            img_orig = Image.alpha_composite(img_orig, overlay)
        except: pass

    # --- AJUSTE PARA NÃO PRECISAR DE SCROLL ---
    max_display_h = 550 
    ratio = max_display_h / real_h
    display_height = max_display_h
    display_width = int(real_w * ratio)
    
    # Limite para não estourar largura em horizontais
    if display_width > 850:
        display_width = 850
        display_height = int(real_h * (display_width / real_w))

    img_display = img_orig.resize((display_width, display_height), Image.Resampling.LANCZOS)
    
    # Criação do Canvas Estilizado
    padding, bar_h = 20, 45
    canvas_w = display_width + (padding * 2)
    canvas_h = display_height + bar_h + (padding * 2)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (18, 18, 24, 255))
    draw = ImageDraw.Draw(canvas)
    canvas.paste(img_display, (padding, padding))
    
    # Barra Branca
    bar_y = padding + display_height
    draw.rectangle([padding, bar_y, padding + display_width, bar_y + bar_h], fill="white")
    
    # Texto das Specs
    ext = image_file.name.split('.')[-1].upper()
    peso_calc = image_file.size/1024/1024
    peso = f"{peso_calc:.2f} MB" if peso_calc > 1 else f"{image_file.size/1024:.0f} KB"
    
    try:
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if not os.path.exists(font_path): font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f_bold = ImageFont.truetype(font_path, 11)
    except: f_bold = ImageFont.load_default()

    ty = bar_y + (bar_h // 2) - 6
    draw.text((padding + 15, ty), f"FORMATO: {ext}", fill="black", font=f_bold)
    draw.text((canvas_w // 2 - 35, ty), f"PESO: {peso}", fill="black", font=f_bold)
    draw.text((canvas_w - padding - 150, ty), f"DIMENSÃO: {real_w}X{real_h}", fill="black", font=f_bold)
    
    return canvas

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
if ferramenta == "Scanner & Safe Areas":
    if arquivo:
        view = process_qa_view(arquivo, SAFE_AREAS[modo], modo, opacidade)
        if view:
            st.image(view)
            st.success("✅ Specs e Proporção validadas.")
    else:
        st.info("Aguardando upload para análise...")

elif ferramenta == "Comparador (V1 vs V2)":
    if v1_file and v2_file:
        col1, col2 = st.columns(2)
        with col1:
            st.image(v1_file, caption="Versão 1", use_container_width=True)
        with col2:
            st.image(v2_file, caption="Versão 2", use_container_width=True)
        
        if st.checkbox("Sobrepor Versões (Blink Test)"):
            img1 = Image.open(v1_file).convert("RGBA")
            img2 = Image.open(v2_file).convert("RGBA").resize(img1.size)
            diff = Image.blend(img1, img2, alpha=0.5)
            st.image(diff, caption="Mix 50/50 das duas versões", use_container_width=True)
    else:
        st.info("Suba dois arquivos para habilitar a comparação.")