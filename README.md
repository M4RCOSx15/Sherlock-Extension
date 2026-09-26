# RASTRO

O **RASTRO** é uma ferramenta de auditoria de dark patterns web com foco no consumidor e no analista de design ético. Inspeciona o DOM e o texto visível de páginas públicas em busca de sinais de manipulação de UX.

## Fase Atual: MVP V1 🚀
A base determinística do MVP e o gate de egress local foram concluídos. A etapa semântica opcional agora aceita Gemini 3.8 Flash e mantém compatibilidade com Qwen. A chamada direta ao Gemini foi validada; ainda falta configurar uma chave local e confirmar o fluxo completo dentro do Docker.

O sistema conta com:
- **Interface Terminal/Cyber:** Uma interface interativa nativa (sem frameworks JS pesados) em HTML/CSS baunilha, servida pela própria API.
- **FastAPI Backend:** Servidor Python extremamente rápido que gerencia requisições e isola erros.
- **Playwright Headless Scraper:** Motor que carrega o DOM com um identificador próprio. O RASTRO não tenta contornar proteções anti-bot.
- **Filtro de destino (defesa em profundidade):** valida a URL inicial e intercepta requests HTTP(S) do navegador para bloquear destinos não públicos. Isso ainda não substitui isolamento de rede contra redirects e DNS rebinding.
- **Scanner Determinístico:** Motor analítico rodando em cima de `BeautifulSoup4` e expressões regulares para quantificar o abuso de UX e retornar um score.
- **LLM opcional (Gemini/Qwen):** Complementa as regras quando `LLM_ENABLED=true`. Envia texto visível limitado, valida as citações retornadas e mantém o modo determinístico como fallback. O score é heurístico, não uma probabilidade calibrada.

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

O servidor de desenvolvimento escuta somente em `127.0.0.1` e não tem isolamento de egress no processo local. A configuração Docker abaixo acrescenta essa barreira, mas ainda depende dos critérios de validação operacional antes de qualquer exposição pública.

## Execução isolada com Docker (Sprint 12)

A configuração Compose coloca o Chromium e as chamadas opcionais ao provedor LLM atrás de um proxy de saída controlado. O gate local foi validado; deploy público continua fora do escopo.

```powershell
docker compose up --build
```

Abra `http://127.0.0.1:8000`. O Compose publica a API somente no loopback do host. Se a sub-rede Docker `172.29.254.0/29` já estiver em uso, altere em conjunto os endereços fixos de `compose.yaml`, `docker/api-entrypoint.sh` e `docker/egress/squid.conf`.

Para habilitar Gemini 3.8 Flash no Docker, configure LLM_ENABLED=true, LLM_PROVIDER=gemini, LLM_API_KEY, LLM_MODEL=gemini-3.8-flash e a base URL generativelanguage.googleapis.com/v1beta/openai/ no .env local. O padrão aguarda 1.800 ms após DOMContentLoaded para SPAs renderizarem texto e envia até 12.000 caracteres ao Gemini; SCRAPER_RENDER_WAIT_MS pode ser ajustado entre 0 e 5.000 ms. LLM_TIMEOUT_SECONDS=30 dá mais tempo à resposta do modelo. Depois execute docker compose up -d --build api. A faixa gratuita do Google pode usar entradas e respostas para melhorar os produtos; envie somente conteúdo público e não sensível. Qwen via DashScope continua compatível. Sem essa configuração, o scanner permanece determinístico.

## Regras e Arquitetura do Projeto
Para detalhes sobre decisões de engenharia, arquitetura e as microsprints planejadas para o RASTRO, consulte a pasta `/docs/antigravity`.

---
*Projeto em evolução constante visando transparência no e-commerce digital.*
