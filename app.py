import streamlit as st
from PIL import Image
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="QA Specs", layout="wide")

# 📐 DETECTAR FORMATO
def detectar_formato(width, height):
    ratio = round(width / height, 2)

    if ratio == 0.56:
        return "Story"
    elif ratio == 1:
        return "Quadrado"
    elif ratio == 1.91:
        return "Feed"
    else:
        return "Fora do padrão"

# 🚀 VEÍCULO
def detectar_veiculo(formato):
    if formato == "Story":
        return "Instagram Stories / TikTok"
    elif formato == "Quadrado":
        return "Instagram Feed"
    elif formato == "Feed":
        return "Facebook / YouTube Ads"
    else:
        return "Formato não identificado"

# 📄 PDF
def gerar_pdf(nome, score, arquivo_nome, tamanho_mb, formato):

    doc = SimpleDocTemplate(nome)
    styles = getSampleStyleSheet()

    elementos = []

    # "LOGO"
    elementos.append(Paragraph("<b>QA Specs</b>", styles['Title']))
    elementos.append(Spacer(1, 12))

    # SCORE
    elementos.append(Paragraph(f"<b>Score:</b> {score}/10", styles['Heading2']))
    elementos.append(Spacer(1, 20))

    veiculo = detectar_veiculo(formato)

    dados = [
        ["Arquivo", arquivo_nome],
        ["Tamanho", f"{round(tamanho_mb,2)} MB"],
        ["Formato", formato],
        ["Veículo sugerido", veiculo]
    ]

    tabela = Table(dados, colWidths=[150, 300])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))

    elementos.append(tabela)

    doc.build(elementos)

# 🎨 UI
st.markdown("""
<style>
body {background:#0f1117;color:white;}

.card {
    background:#1c1f26;
    padding:20px;
    border-radius:16px;
    margin-bottom:20px;
    box-shadow: 0 6px 30px rgba(0,0,0,0.4);
}

.aprovado {color:#00ffae;}
.alerta {color:#ffd166;}
.reprovado {color:#ff4d6d;}

.score {
    font-size:50px;
    font-weight:700;
}

/* BOTÃO ROXO */
.stButton > button {
    background: linear-gradient(135deg, #6c5ce7, #a29bfe);
    color: white;
    border: none;
    padding: 12px 18px;
    border-radius: 12px;
    font-weight: 600;
    transition: 0.2s;
}

.stButton > button:hover {
    transform: scale(1.03);
    opacity: 0.9;
}
</style>
""", unsafe_allow_html=True)

st.title("QA Specs")

arquivo = st.file_uploader("Upload", type=["png","jpg","jpeg","mp4","mov"])

score = 0
formato = "N/A"
tamanho_mb = 0

# 🖼️ ANÁLISE
if arquivo:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    tamanho_mb = arquivo.size / (1024 * 1024)

    st.write(f"📄 Nome: {arquivo.name}")
    st.write(f"📦 Tamanho: {round(tamanho_mb,2)} MB")

    # 📦 PESO
    if tamanho_mb <= 200:
        score += 3
    else:
        st.error("Arquivo maior que 200MB")

    arquivo.seek(0)

    # 🖼️ IMAGEM
    if "image" in arquivo.type:
        imagem = Image.open(arquivo)
        st.image(imagem, width='stretch')

        largura, altura = imagem.size
        formato = detectar_formato(largura, altura)

        st.write(f"📐 {largura}x{altura}")
        st.write(f"🎯 {formato}")

        if formato != "Fora do padrão":
            score += 3
        else:
            st.warning("Formato fora do padrão")

        if largura >= 1080:
            score += 2

    # 🎥 VÍDEO
    elif "video" in arquivo.type:
        st.video(arquivo)
        score += 2
        formato = "Vídeo"

    # 📁 NOME
    if "_" in arquivo.name:
        score += 2

    st.markdown('</div>', unsafe_allow_html=True)

score = min(score, 10)

# 🎯 RESULTADO
st.markdown('<div class="card">', unsafe_allow_html=True)

if score >= 8:
    status = "aprovado"
    label = "APROVADO"
elif score >= 5:
    status = "alerta"
    label = "ATENÇÃO"
else:
    status = "reprovado"
    label = "REPROVADO"

st.markdown(f"<p class='score {status}'>{score}/10</p>", unsafe_allow_html=True)
st.markdown(f"<p class='{status}'>{label}</p>", unsafe_allow_html=True)

st.progress(score / 10)

st.markdown('</div>', unsafe_allow_html=True)

# 📄 DOWNLOAD PDF
if arquivo:
    if st.button("Gerar relatório"):

        nome = f"qa_specs_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

        gerar_pdf(nome, score, arquivo.name, tamanho_mb, formato)

        with open(nome, "rb") as f:
            st.download_button(
                "Baixar PDF",
                f,
                file_name=nome,
                mime="application/pdf"
            )