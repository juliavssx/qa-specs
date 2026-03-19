import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from moviepy.editor import VideoFileClip
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
    "YouTube Horizontal": {"file": "YTHorizontal.svg", "width": 1920, "height": 1080},
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
    """Retorna o tamanho do arquivo em bytes"""
    if hasattr(file, 'size'):
        return file.size
    return 0

def get_file_size_formatted(size_bytes):
    """Retorna o peso do arquivo formatado"""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def validate_total_size(files):
    """Valida se o tamanho total dos arquivos não excede o limite"""
    total_bytes = sum([get_file_size_bytes(f) for f in files])
    total_mb = total_bytes / (1024 * 1024)
    if total_mb > MAX_UPLOAD_SIZE_MB:
        st.error(f"❌ Tamanho total excede o limite de {MAX_UPLOAD_SIZE_MB}MB (Atual: {total_mb:.1f}MB)")
        return False
    return True

def analyze_video(uploaded_file):
    """Analisa vídeo usando moviepy (não precisa de libGL)"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp.write(uploaded_file.read())
        video_path = tmp.name
    
    try:
        clip = VideoFileClip(video_path)
        width = clip.size[0]
        height = clip.size[1]
        fps = clip.fps
        clip.close()
    except Exception as e:
        os.unlink(video_path)
        uploaded_file.seek(0)
        raise e
    
    os.unlink(video_path)
    uploaded_file.seek(0)
    return width, height, round(fps, 2)

def apply_safe_area(img_orig, config, opacity):
    """Aplica overlay de safe area na imagem com fallback"""
    real_w, real_h = img_orig.size
    overlay_filename = config.get("file")
    
    # Se não há arquivo configurado (ex: Google/DCM), retorna imagem original
    if not overlay_filename:
        return img_orig
    
    # Lista de possíveis locais para os arquivos (fallback)
    possible_paths = [
        overlay_filename,
        f"safe_areas/{overlay_filename}",
        f"assets/{overlay_filename}",
        os.path.join(os.path.dirname(__file__), "safe_areas", overlay_filename)
    ]
    
    for path in possible_paths:
        if path and os.path.exists(path):
            overlay = Image.open(path).convert("RGBA")
            overlay = overlay.resize((real_w, real_h), Image.Resampling.LANCZOS)
            alpha = overlay.getchannel('A')
            new_alpha = alpha.point(lambda i: i * opacity)
            overlay.putalpha(new_alpha)
            return Image.alpha_composite(img_orig.convert("RGBA"), overlay)
    
    # Se não encontrar, avisa o usuário
    st.caption("ℹ️ Safe area não encontrada - mostrando apenas imagem original")
    return img_orig

def clean_size_format(raw_meta):
    """Limpa e formata meta tag de tamanho"""
    if not raw_meta: 
        return "⚠️ N/A"
    clean = raw_meta.lower().replace("width=", "").replace("height=", "").replace(" ", "").replace(",", "x")
    return clean

def validate_html5_package(zip_file):
    """Valida pacote HTML5"""
    report = {
        "html_found": False, "click_tag": False, "size_meta": None, 
        "file_path": "", "raw_html": "", "type": "Desconhecido", 
        "kb_size": zip_file.size / 1024,
        "files_list": []
    }
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            all_files = z.namelist()
            report["files_list"] = [f for f in all_files if not f.startswith('__MACOSX')]
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
    except Exception as e:
        st.warning(f"Erro ao analisar ZIP: {str(e)}")
    # Reset file pointer
    zip_file.seek(0)
    return report

def process_file(arquivo, modo, opacidade):
    """Processa um único arquivo e retorna os resultados"""
    ext = arquivo.name.split('.')[-1].lower()
    config = SAFE_AREAS[modo]
    resultado = {
        "nome": arquivo.name,
        "tipo": ext,
        "tamanho": get_file_size_bytes(arquivo),
        "detalhes": {}
    }
    
    # Processamento por tipo
    if ext == "zip":
        resultado["detalhes"] = validate_html5_package(arquivo)
    elif ext in ["mp4", "mov"]:
        try:
            w, h, fps = analyze_video(arquivo)
            resultado["detalhes"] = {
                "resolucao": f"{w}x{h}",
                "fps": fps,
                "fps_ok": abs(fps - 29.97) < 0.5 or abs(fps - 30) < 0.5
            }
        except Exception as e:
            resultado["erro"] = str(e)
    elif ext in ["png", "jpg", "jpeg"]:
        try:
            img = Image.open(arquivo)
            resultado["detalhes"] = {
                "dimensoes": f"{img.width}x{img.height}",
                "img_obj": img,
                "config": config,
                "opacidade": opacidade
            }
        except Exception as e:
            resultado["erro"] = str(e)
    
    return resultado

def display_file_result(resultado, modo):
    """Exibe o resultado do processamento de um arquivo"""
    with st.container():
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"**📄 {resultado['nome']}**")
            st.caption(f"Tipo: {resultado['tipo'].upper()} | Tamanho: {get_file_size_formatted(resultado['tamanho'])}")
        
        with col2:
            if "erro" in resultado:
                st.error(f"❌ Erro: {resultado['erro']}")
            elif resultado['tipo'] == "zip":
                report = resultado["detalhes"]
                if report["html_found"]:
                    st.success(f"✅ HTML5 - {report['type']}")
                    with st.expander("Ver detalhes do ZIP"):
                        st.metric("Peso do ZIP", f"{report['kb_size']:.1f} KB")
                        st.metric("ClickTag", "✅ OK" if report["click_tag"] else "❌ AUSENTE")
                        if report["size_meta"]:
                            st.metric("Formato", report["size_meta"])
                        if report["files_list"]:
                            st.write("Arquivos no ZIP:", ", ".join(report["files_list"][:5]))
                else:
                    st.error("❌ Nenhum arquivo HTML encontrado")
            elif resultado['tipo'] in ["mp4", "mov"]:
                det = resultado["detalhes"]
                st.metric("Resolução", det["resolucao"])
                fps_status = "✅ OK" if det["fps_ok"] else "❌ Erro"
                st.metric("FPS", f"{det['fps']}", delta=fps_status)
                if modo == "Adstream/TV (Manual)":
                    st.info("**Checklist Adstream:**\n- Loudness: -23/-24 LUFS\n- Timeline: Claquete+Black")
            elif resultado['tipo'] in ["png", "jpg", "jpeg"]:
                det = resultado["detalhes"]
                img_with_safe = apply_safe_area(det["img_obj"], det["config"], det["opacidade"])
                st.image(img_with_safe, use_container_width=True)
                st.caption(f"Dimensões: {det['dimensoes']}")

# --- Sidebar ---
with st.sidebar:
    st.title("🛠️ Smart QA Toolbox")
    
    # CSS customizado para melhor aparência
    st.markdown("""
    <style>
    .stRadio > div {
        padding: 10px;
        background-color: #1E1E1E;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    ferramenta = st.radio(
        "Selecione a Ferramenta:", 
        ["Scanner & Safe Areas", "Comparador (V1 vs V2)"],
        key="ferramenta_selector"
    )
    
    if ferramenta == "Scanner & Safe Areas":
        st.markdown("---")
        st.markdown("### 📤 Upload de Múltiplos Arquivos")
        
        arquivos = st.file_uploader(
            "Arraste ou selecione os assets:", 
            type=["png", "jpg", "jpeg", "mp4", "mov", "zip"],
            accept_multiple_files=True,
            key="multi_uploader",
            help=f"Máximo de {MAX_FILES} arquivos por vez"
        )
        
        if arquivos and len(arquivos) > MAX_FILES:
            st.warning(f"⚠️ Muitos arquivos! Máximo: {MAX_FILES}")
            arquivos = arquivos[:MAX_FILES]
        
        if arquivos and not validate_total_size(arquivos):
            arquivos = None
        
        modo = st.selectbox(
            "Plataforma / Destino:", 
            list(SAFE_AREAS.keys()),
            key="modo_selector"
        )
        
        # Verifica se há imagens para mostrar controle de opacidade
        tem_imagens = arquivos and any(
            f.name.split('.')[-1].lower() in ["png", "jpg", "jpeg"] 
            for f in arquivos
        )
        
        opacidade = 0.70
        if tem_imagens:
            opacidade = st.slider(
                "Opacidade da Safe Area:", 
                0.0, 1.0, 0.70,
                key="opacidade_slider"
            )
    
    else:  # Comparador
        st.markdown("---")
        st.markdown("### 🔍 Comparar Duas Versões")
        v1 = st.file_uploader("Versão 1 (Antiga):", type=["png", "jpg", "jpeg"], key="v1")
        v2 = st.file_uploader("Versão 2 (Nova):", type=["png", "jpg", "jpeg"], key="v2")

# --- Área Principal ---
st.markdown("# 🎯 QA Hub - Smart Specs")
st.markdown("---")

if ferramenta == "Scanner & Safe Areas":
    if not arquivos:
        st.info("👈 **Selecione os arquivos na barra lateral para começar**")
        
        # Exemplo de uso
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
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Processa cada arquivo
        for i, arquivo in enumerate(arquivos):
            status_text.text(f"Processando: {arquivo.name}...")
            
            # Processa o arquivo
            resultado = process_file(arquivo, modo, opacidade)
            
            # Exibe o resultado
            with st.container():
                st.markdown(f"### 📁 Arquivo {i+1} de {len(arquivos)}")
                display_file_result(resultado, modo)
                st.markdown("---")
            
            # Atualiza progresso
            progress_bar.progress((i + 1) / len(arquivos))
        
        # Limpa status
        status_text.empty()
        progress_bar.empty()
        
        # Botão para limpar todos os arquivos (versão melhorada)
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Limpar todos", type="primary", use_container_width=True):
                # Limpa TODOS os estados relacionados a uploads
                keys_to_clear = [k for k in st.session_state.keys() 
                                 if 'uploader' in k or 'arquivo' in k or 'multi' in k]
                for key in keys_to_clear:
                    del st.session_state[key]
                st.rerun()

elif ferramenta == "Comparador (V1 vs V2)":
    if not v1 or not v2:
        st.info("👈 **Selecione as duas versões na barra lateral para comparar**")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            img1 = Image.open(v1)
            st.image(img1, caption=f"V1 - {get_file_size_formatted(get_file_size_bytes(v1))}", 
                    use_container_width=True)
            st.metric("Dimensões V1", f"{img1.width}x{img1.height}")
        
        with col2:
            img2 = Image.open(v2)
            st.image(img2, caption=f"V2 - {get_file_size_formatted(get_file_size_bytes(v2))}", 
                    use_container_width=True)
            st.metric("Dimensões V2", f"{img2.width}x{img2.height}")
        
        # Comparação rápida
        if img1.size == img2.size:
            st.success("✅ Mesmas dimensões")
        else:
            st.warning("⚠️ Dimensões diferentes")
        
        diff_percent = abs(get_file_size_bytes(v1) - get_file_size_bytes(v2)) / max(get_file_size_bytes(v1), get_file_size_bytes(v2)) * 100
        st.metric("Diferença de tamanho", f"{diff_percent:.1f}%")

# --- Footer ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 10px;'>
        QA Hub - Smart Specs v2.0 | Upload múltiplo suportado | Limite: {}MB
    </div>
    """.format(MAX_UPLOAD_SIZE_MB),
    unsafe_allow_html=True
)