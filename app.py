import streamlit as st
from PIL import Image
import cv2
import tempfile
import os

# --- Configuração da Página ---
st.set_page_config(page_title="QA Hub - Smart Specs", layout="wide")

SAFE_AREAS = {
    "Adstream/TV (Manual)": {"width": 1920, "height": 1080, "fps": 29.97},
    "YouTube Horizontal": {"width": 1920, "height": 1080},
    "YouTube Shorts": {"width": 1080, "height": 1920},
    "Meta Reel": {"width": 1080, "height": 1920}
}

def analyze_video(uploaded_file):
    """Extrai metadados reais do vídeo usando OpenCV"""
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

# --- Interface Sidebar ---
with st.sidebar:
    st.title("🛠️ Smart QA Toolbox")
    ferramenta = st.radio("Selecione:", ["Scanner & Safe Areas", "Comparador"])
    arquivo = st.file_uploader("Upload do Asset:", type=["png", "jpg", "mp4", "mov"])
    modo = st.selectbox("Plataforma:", list(SAFE_AREAS.keys()))

# --- Área Principal ---
if arquivo:
    ext = arquivo.name.split('.')[-1].lower()
    col_img, col_spacer, col_specs = st.columns([1.5, 0.1, 0.6])

    if ext in ["mp4", "mov"]:
        # LEITURA REAL DAS SPECS
        v_w, v_h, v_fps = analyze_video(arquivo)
        
        with col_img:
            st.video(arquivo)
            
        with col_specs:
            st.markdown("### 🔍 Validação Técnica Adstream")
            
            # Validação de Resolução [cite: 5, 17]
            res_ok = (v_w == 1920 and v_h == 1080)
            st.metric("Resolução", f"{v_w}x{v_h}", delta="✅ OK" if res_ok else "❌ ERRO", delta_color="normal")
            
            # Validação de Frame Rate [cite: 7, 19]
            fps_ok = (abs(v_fps - 29.97) < 0.1)
            st.metric("Frame Rate", f"{v_fps} fps", delta="✅ OK" if fps_ok else "❌ ERRO", delta_color="normal")

            if modo == "Adstream/TV (Manual)":
                st.markdown("---")
                st.markdown("#### 🚩 Checklist Obrigatório (PDF)")
                
                # Check de Nomenclatura [cite: 52]
                if "-" in arquivo.name and len(arquivo.name) > 10:
                    st.success("✅ Nomeclatura: Padrão ClockNumber detectado.")
                else:
                    st.error("❌ Erro Nome: Use AGE-MAR-PRO-030-003")

                st.info(f"""
                **Requisitos Adstream HD:**
                * **Codec:** XDCAM HD 422 ou ProRes 422 HQ [cite: 4, 15]
                * **Áudio:** 48kHz / 24 bits [cite: 10, 11]
                * **Loudness:** -23 a -24 LUFS [cite: 46]
                * **Timeline:** Claquete (5s) + Black (2s) [cite: 71, 72]
                """)
    else:
        # Lógica de Imagem mantida...
        img = Image.open(arquivo)
        with col_img: st.image(img, use_container_width=True)
        with col_specs: st.metric("Dimensões", f"{img.width}x{img.height}")