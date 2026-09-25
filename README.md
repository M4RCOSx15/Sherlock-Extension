# RASTRO_

**Scanner de padrões escuros e copywriting manipulativo em páginas web.**

> Investigue sinais de pressão e padrões de manipulação escondidos na experiência de uma página.

---

## O que é o RASTRO?

RASTRO é um SaaS web de auditoria: você cola uma URL, o sistema analisa a página e devolve um relatório de *dark patterns* — técnicas de design e copywriting que manipulam usuários contra seus próprios interesses (falsa escassez, urgência fabricada, indução à culpa, etc.).

---

## Estado Atual: PRÉ-MVP

O projeto está em desenvolvimento ativo. Veja o status detalhado em [`docs/antigravity/STATE.md`](docs/antigravity/STATE.md).

### O que já existe
- Interface visual estática (`frontend/index.html`) com estética terminal/hacker
- Simulação de análise (dados mockados — nenhuma URL é realmente acessada)

### O que ainda não existe
- Backend real (FastAPI + Playwright)
- Análise determinística de dark patterns
- Integração com LLM

---

## Como rodar (estado atual)

Sem dependências. Apenas abra o arquivo no navegador:

```bash
# Opção 1: abrir direto
start frontend/index.html   # Windows
open frontend/index.html    # macOS

# Opção 2: servidor local simples (Python)
python -m http.server 8080
# Acesse: http://localhost:8080/frontend/
```

---

## Stack Técnico (planejado)

| Camada | Tecnologia |
|---|---|
| Frontend | HTML / CSS / JS puro (sem framework) |
| Backend | Python 3.12+ + FastAPI |
| Scraping | Playwright |
| LLM (Fase 2) | Gemini Flash ou Qwen via OpenRouter |
| Deploy (futuro) | Docker + Oracle Cloud VPS (ARM64) |

---

## Setup para desenvolvimento (futuro)

```bash
# 1. Copiar variáveis de ambiente
cp .env.example .env
# Edite o .env com seus valores reais

# 2. Criar ambiente virtual Python (a partir da Sprint 6)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 3. Instalar dependências (a partir da Sprint 6)
pip install -r backend/requirements.txt
```

---

## Documentação do Projeto (para o agente Antigravity)

- [`docs/antigravity/STATE.md`](docs/antigravity/STATE.md) — Estado atual e próximos passos
- [`docs/antigravity/MICROSPRINTS.md`](docs/antigravity/MICROSPRINTS.md) — Roteiro de desenvolvimento
- [`docs/antigravity/DECISOES-TECNICAS.md`](docs/antigravity/DECISOES-TECNICAS.md) — Decisões de arquitetura
- [`docs/antigravity/HANDOFF.md`](docs/antigravity/HANDOFF.md) — Checkpoint de sessão

---

*Projeto em desenvolvimento. Artefatos legados de extensão de Chrome (`manifest.json`, `popup.js`, `popup.html`) na raiz podem ser ignorados.*
