import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuração da Página ---
st.set_page_config(page_title="QA Hub - Smart Specs", layout="centered")

# Dicionário com ficheiros e dimensões esperadas
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
    """Verifica se a proporção da imagem bate com o esperado"""
    actual_ratio = img.width / img.height
    target_ratio = target_w / target_h
    # Tolerância de 1% para pequenas variações
    return abs(actual_ratio - target_ratio) < 0.01

def process_qa_view(image_file, config, modo_nome):
    img_orig = Image.open(image_file).convert("RGBA")
    real_w, real_h = img_orig.size
    
    # --- BARREIRA DE VALIDAÇÃO ---
    if not validate_dimensions(img_orig, config["width"], config["height"]):
        st.error(f"⚠️ **Formato Incorreto!** A imagem enviada não possui a proporção correta para {modo_nome}. Esperado: {config['width']}x{config['height']}.")
        return None

    # Aplica Safe Area
    overlay_filename = config["file"]
    if overlay_filename and os.path.exists(overlay_filename):
        try:
            overlay = Image.open(overlay_filename).convert("RGBA")
            overlay = overlay.resize((real_w, real_h), Image.Resampling.LANCZOS)
            img_orig = Image.alpha_composite(img_orig, overlay)
        except:
            pass

    # Redimensionamento para Display (Visualização no Site)
    display_width = 750
    ratio = display_width / real_w
    display_height = int(real_h * ratio)
    img_display = img_orig.resize((display_width, display_height), Image.Resampling.LANCZOS)
    
    # Criação do Canvas Estilizado (Igual à sua referência)
    padding = 20
    bar_h = 50
    canvas_w = display_width + (padding * 2)
    canvas_h = display_height + bar_h + (padding * 2)
    
    # Cor de fundo escura (Dark Mode)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (18, 18, 24, 255))
    draw = ImageDraw.Draw(canvas)
    
    # Cola a imagem centralizada
    canvas.paste(img_display, (padding, padding))
    
    # Desenha a Barra Branca de Specs
    bar_y_start = padding + display_height
    draw.rectangle([padding, bar_y_start, padding + display_width, bar_y_start + bar_h], fill="white")
    
    # Informações de Texto
    ext = image_file.name.split('.')[-1].upper()
    peso_calc = image_file.size/1024/1024
    peso = f"{peso_calc:.2f} MB" if peso_calc > 1 else f"{image_file.size/1024:.0f} KB"
    
    try:
        # Tenta carregar uma fonte Bold do sistema
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if not os.path.exists(font_path):
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f_bold = ImageFont.truetype(font_path, 14)
    except:
        f_bold = ImageFont.load_default()

    # Escreve os textos na barra branca
    text_y = bar_y_start + (bar_h // 2) - 7
    draw.text((padding + 20, text_y), f"FORMATO: {ext}", fill="black", font=f_bold)
    draw.text((canvas_w // 2 - 40, text_y), f"PESO: {peso}", fill="black", font=f_bold)
    draw.text((canvas_w - padding - 185, text_y), f"DIMENSÃO: {real_w}X{real_h}", fill="black", font=f_bold)
    
    return canvas

# --- Interface Streamlit ---
st.title("🚀 QA Hub - Smart Specs")

with st.sidebar:
    st.header("Configurações")
    modo = st.selectbox("Selecione o Veículo:", list(SAFE_AREAS.keys()))
    arquivo = st.file_uploader("Suba o arquivo:", type=["png", "jpg", "jpeg"])

if arquivo:
    # Chama a função de processamento
    view = process_qa_view(arquivo, SAFE_AREAS[modo], modo)
    
    if view:
        st.image(view, use_container_width=True)
        st.success(f"✅ Preview gerado com sucesso!")