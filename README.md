# RASTRO

Auditor de dark patterns em páginas públicas. Você cola uma URL, o RASTRO abre a página num Chromium isolado, lê o que renderizou e devolve os sinais encontrados: evidências, gravidade e um score de risco contextual.

## Como funciona

1. Você manda a URL pela interface.
2. O backend abre a página com Playwright e espera o DOM estabilizar (mínimo de 2s, teto de 3.5s configurável).
3. Regras determinísticas procuram padrões no texto e nos elementos renderizados: urgência, escassez, confirmshaming, ancoragem de preço, pré-seleção, overlay e assimetria de consentimento.
4. Se o Gemini estiver ligado, roda uma análise semântica por cima. Se falhar ou não estiver configurado, o resultado determinístico volta normal.

O score é heurístico — soma pontos por severidade (5/10/20/30, até 100). Não é probabilidade nem prova de intenção; serve pra indicar o que vale revisar.

## Stack

- **Frontend:** HTML/CSS/JS puro, servido pela própria API. Histórico de até 10 análises fica no `localStorage` e os relatórios Markdown são gerados no navegador — nada disso passa pelo servidor.
- **Backend:** Python + FastAPI.
- **Scraping:** Playwright/Chromium.
- **LLM (opcional):** Gemini (ou Qwen), recebe só um recorte limitado de texto — nunca o HTML inteiro.
- **Isolamento:** Docker Compose com proxy de saída. A API não tem saída direta pra internet e só expõe porta em `127.0.0.1`.

## Rodando

Precisa do Docker Desktop aberto. Na raiz do projeto:

```powershell
docker compose up -d --build api
docker compose ps
```

Espera `api` e `egress-proxy` ficarem `healthy` e abre:

- App: <http://127.0.0.1:8000/>
- Swagger: <http://127.0.0.1:8000/docs>

Comandos do dia a dia:

```powershell
docker compose logs --tail=100 api   # ver logs
docker compose restart               # reinicia sem rebuild
docker compose down                  # para e remove os containers
```

Mudou código? Roda `docker compose up -d --build api` de novo. Mudou o front? `Ctrl+F5` na página pra limpar cache.

## Gemini (opcional)

Vem desligado por padrão. Pra ativar, copia o `.env.example` pra `.env` e ajusta:

```dotenv
LLM_ENABLED=true
LLM_API_KEY=sua_chave
```

Reconstroi a API depois. A chave fica só no backend — não aparece no front, nos relatórios nem nos logs. Setup completo em [`docs/antigravity/CREDENCIAIS-E-SETUP.md`](docs/antigravity/CREDENCIAIS-E-SETUP.md).

## Sem Docker

Dá pra rodar em Python puro, mas sem o isolamento de rede do Compose — evita analisar URL que você não controla:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
playwright install chromium
python run_server.py
```

(O `run_server.py` existe porque o Uvicorn + Playwright brigam com o loop de eventos do Windows — não chame o uvicorn direto.)

## Docs

- [`docs/antigravity/STATE.md`](docs/antigravity/STATE.md) — onde o projeto tá e o que falta validar
- [`docs/antigravity/MICROSPRINTS.md`](docs/antigravity/MICROSPRINTS.md) — histórico de sprints e critérios de aceite
- [`docs/api-contract.md`](docs/api-contract.md) — contrato da API

## Status

MVP local validado. Deploy público, contas e sincronização de relatórios ainda não existem — são fases futuras com escopo próprio.
