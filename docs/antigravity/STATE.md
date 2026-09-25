# RASTRO - Estado Atual do Projeto

*Este arquivo deve ser atualizado pelo agente Antigravity no final de cada sprint para manter o contexto vivo caso a sessão caia ou o limite de tokens seja alcançado.*

- **Data da Última Atualização**: 2026-09-25
- **Sprint Atual/Concluída**: **Sprint 8 — CONCLUÍDA** (Playwright integrado — scraping real de páginas públicas).
- **Fase**: Fundação e Protótipo (Com Scraping Real, Sem Análise).

## O Que Já Funciona
- Interface interativa completa: `frontend/index.html` — máquina de estados JS com mocks alinhados ao contrato `POST /api/scan`. `RISK_LABELS`, `MOCK_ERROR` com `code: PAGE_UNREACHABLE`, `findings[].evidence`, `findings[].risk_level`. TODO comentado para Sprint 10.
- **Sprint 5 — Contrato definido:** `docs/api-contract.md` cobre request, 5 respostas de erro, schema de `Finding`, thresholds de `risk_level`, catálogo de 8 `id` de findings para Fase 1.
- **Sprint 4 — Mocks:** 3 cenários rotativos, `setState()`, `resetUI()`, `showSuccess()`, `showError()`. Favicon `favicon.jpg`. Badge `[ SIMULAÇÃO ]`.
- **Sprint 3 — Polimentos:** status dot verde/rosa, breakpoints, acessibilidade.
- `.gitignore`, `.env.example`, `README.md`, `backend/.gitkeep` (Sprint 1).

## O Que Ainda É Simulado / Não Existe
- Toda a lógica de análise é 100% mockada no frontend (setTimeout, dados estáticos).
- Não existe backend, API, scraper, nem banco de dados.
- O `manifest.json` e `popup.js` na raiz são de uma extensão de navegador antiga ("Sherlock Extension") e **devem ser ignorados**.

## Problemas Ativos / Bloqueios
- Nenhum bloqueio crítico.

## Como Rodar o Projeto Atualmente
*(Abrir o HTML diretamente no navegador — sem dependências)*
```bash
start frontend/index.html   # Windows
open frontend/index.html    # macOS/Linux
```

## Próximo Passo
- Aguardando aprovação do usuário para iniciar a **Sprint 4** (Fluxo de interface com simulação explícita: estados idle/analisando/erro/sucesso via JS, sem backend real).

