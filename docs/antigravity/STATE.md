# RASTRO - Estado Atual do Projeto

*Este arquivo deve ser atualizado pelo agente Antigravity no final de cada sprint para manter o contexto vivo caso a sessão caia ou o limite de tokens seja alcançado.*

- **Data da Última Atualização**: 2026-09-25
- **Sprint Atual/Concluída**: **Sprint 4 — CONCLUÍDA** (Fluxo de interface com simulação explícita — mocks JS).
- **Fase**: Fundação e Protótipo (Sem Backend Funcional).

## O Que Já Funciona
- Interface interativa completa: `frontend/index.html` — máquina de estados JS com 4 estados explícitos (idle, analisando, falha simulada ~25%, sucesso com 3 cenários rotativos de findings fictícios). Botão bloqueado durante análise. Botão "↺ NOVA ANÁLISE" / "↺ TENTAR OUTRA URL" para reset.
- **Sprint 4 — Mocks implementados:** `MOCK_SCENARIOS` com 3 conjuntos de findings, `setState()`, `resetUI()`, `showSuccess()`, `showError()`. Nenhuma URL é acessada. Badge `[ SIMULAÇÃO ]` visível nos cards.
- **Sprint 3 — Polimentos:** favicon local, meta description, status dot verde (idle) → rosa (scanning), font-sizes corrigidos, `cursor: not-allowed`, `autocomplete="off"`, breakpoints 680px/520px.
- `.gitignore`, `.env.example`, `README.md`, `backend/.gitkeep` criados (Sprint 1).
- Documentação completa em `docs/antigravity/`.

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

