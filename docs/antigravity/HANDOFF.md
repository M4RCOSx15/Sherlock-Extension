# RASTRO — Handoff de Sessão

## Resumo Executivo
O projeto do SaaS RASTRO (Auditor de Dark Patterns Web) concluiu oficialmente a sua **Fase 1 (MVP)**, totalizando 10 microsprints de desenvolvimento de sucesso. A plataforma baseia-se numa stack puramente local: frontend Vanilla HTML/CSS/JS (design hacker/terminal) e backend Python (FastAPI + Playwright).

Neste ponto, o sistema é capaz de receber uma URL na interface web, despachar um worker (navegador headless) seguro por meio de blindagem SSRF, ler todo o DOM da página alvo, e rodar regras determinísticas para extrair abusos UX (como falsas urgências, checkboxes ocultos, e ancoragens de preço fajutas), devolvendo um score em tempo real.

## Progresso Atual (Fase 1 - MVP Concluída)
- **Frontend V1 Pronto:** Interface visual totalmente funcional, integrada ao backend e lidando nativamente com estados de erro da API. Textos simulados foram permanentemente substituídos pelos dados da API (Sprint 10 concluída).
- **Backend API & Motor:** 
  - FastAPI estruturado e servindo requisições (`/api/scan`).
  - Playwright integrado operando em contexto bloqueado (otimizado).
  - Segurança contra acesso a redes locais implementada (SSRF guard).
  - Motor analítico em `analyzer.py` executando pontuação com pesos e regras estruturadas em CSS/Regex.
- **Ambiente Resolvido:** Problemas crônicos do ecossistema Windows (Playwright vs. Uvicorn Asyncio loops) foram pacificados pela criação do arquivo `run_server.py`.

## Como Rodar Localmente (Obrigatório)
Abra um terminal PowerShell na raiz do projeto (`dark-plugin`) e rode:
```powershell
.venv\Scripts\activate
python run_server.py
```
* **Aplicação Web:** `http://localhost:8000`
* **Swagger API:** `http://localhost:8000/docs`

## Próximos Desafios (Roadmap / Fases 2+)
Se houver uma próxima sessão ou retomada do desenvolvimento, os vetores de avanço seriam:
1. **Fase de IA Generativa:** Integrar a API LLM (ex: OpenRouter, OpenAI, Gemini) ao pipeline após o motor determinístico rodar, para injetar análise de semântica e intenção no HTML que as Regex não pegam.
2. **Camada de Dados:** Atualmente, nada é salvo (Stateless). Para ser um SaaS, é necessário introduzir um banco de dados (SQLite, Postgres) e a infraestrutura de login/autenticação.
3. **Módulo de Deploy:** Criar scripts/Dockerfiles para viabilizar hospedagem em VPS (Linux).

## Dicas Rápidas
- *Windows Asyncio:* Nunca use `uvicorn backend.main:app` direto sem entender o impacto no loop do SO. Confie no `run_server.py`.
- *Playwright:* Não faça scraping sem acionar o `check_ssrf()`. Sempre isole as sessões do navegador (`BrowserContext`).
- *Acesso Remoto:* Lembre-se, o backend faz as requests do lugar onde ele está hospedado. Em nuvem, certifique-se que o IP tem liberação para scraping.
