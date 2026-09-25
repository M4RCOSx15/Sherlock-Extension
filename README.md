# RASTRO

O **RASTRO** é uma ferramenta de auditoria de dark patterns web com foco no consumidor e no analista de design ético. Funciona como um SaaS que inspeciona o front-end (DOM/HTML) de páginas públicas em busca de sinais de manipulação de UX (urgência falsa, ancoragem agressiva, confirmshaming, popups intrusivos).

## Fase Atual: MVP V1 🚀
A **Fase 1** foi completamente desenvolvida. O repositório contém a versão final e local do MVP (Minimum Viable Product).

O sistema conta com:
- **Interface Terminal/Cyber:** Uma interface interativa nativa (sem frameworks JS pesados) em HTML/CSS baunilha, servida pela própria API.
- **FastAPI Backend:** Servidor Python extremamente rápido que gerencia requisições e isola erros.
- **Playwright Headless Scraper:** Motor que acessa o site-alvo anonimamente para evitar defesas anti-bot, focado apenas no carregamento do DOM.
- **SSRF Shield:** Barreira rigorosa que previne varreduras contra sua rede local, roteadores ou serviços sensíveis na nuvem (Proteção contra Server-Side Request Forgery).
- **Scanner Determinístico:** Motor analítico rodando em cima de `BeautifulSoup4` e expressões regulares para quantificar o abuso de UX e retornar um score.

## Pré-requisitos
- **Sistema Operacional:** Funciona em Windows, macOS ou Linux.
- **Python:** 3.10 ou superior.

## Como Executar Localmente
O sistema foi configurado para resolver conflitos clássicos de I/O de loop do Windows nativamente por meio do `run_server.py`.

1. Crie seu ambiente virtual (caso ainda não exista) e ative-o:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Instale as dependências e o navegador do Playwright:
   ```powershell
   pip install -r backend/requirements.txt
   playwright install chromium
   ```
3. Inicie a aplicação de forma segura através do script base:
   ```powershell
   python run_server.py
   ```
4. Acesse:
   - **Frontend UI**: [http://localhost:8000](http://localhost:8000)
   - **API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Regras e Arquitetura do Projeto
Para detalhes sobre decisões de engenharia, arquitetura e as microsprints planejadas para o RASTRO, consulte a pasta `/docs/antigravity`.

---
*Projeto em evolução constante visando transparência no e-commerce digital.*
