# 📑 Changelog - QA Hub: Smart Specs

Arquivo de histórico de versões e atualizações técnicas do projeto.

---

## [3.0.0] - 2026-03-19
### ✨ Novidades
- **Bulk Upload:** Suporte para seleção e processamento de múltiplos arquivos simultaneamente.
- **Botão Limpar Tudo:** Reset rápido da interface sem necessidade de F5.
- **Nova Safe Area:** Adicionada máscara oficial do YouTube Horizontal (1920x1080).

### 🔧 Correções Técnicas
- **Fix (Pillow):** Substituição de ativos SVG por PNG para evitar o erro `UnidentifiedImageError`.
- **UI/UX:** Padronização da tipografia para Arial Bold e centralização do bloco de specs.
- **Cloud Sync:** Sincronização de repositório via `git pull --rebase` para estabilidade do deploy.

---

## [2.0.0] - 2026-03-15
### ✨ Novidades
- **Deploy Oficial:** Migração do ambiente local para o Streamlit Cloud.
- **Validador HTML5:** Implementação de leitura de `.zip` e extração de `clickTag`.
- **Limite de Peso:** Alerta automático para arquivos acima de 150KB.

---

## [1.0.0] - 2026-03-10
### 🌱 Lançamento
- **MVP:** Protótipo inicial com checagem de dimensões de imagem e vídeo via OpenCV.
- **Safe Areas Iniciais:** Instagram (Stories/Reels) e TikTok.
