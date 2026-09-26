# RASTRO — Handoff de Sessão

## Resumo Executivo
O projeto do SaaS RASTRO (Auditor de Dark Patterns Web) concluiu as Sprints 0–13. A Sprint 13 foi validada no fluxo completo do Docker: o usuário confirmou uma análise híbrida com Gemini 3.8 Flash em mercadolivre.com.br, com regras determinísticas como fallback. A plataforma usa frontend Vanilla HTML/CSS/JS e backend Python (FastAPI + Playwright). O fluxo não está pronto para exposição pública.

O sistema recebe uma URL pela interface, carrega a página com Playwright, filtra requests por destino e aplica regras determinísticas ao DOM. A Sprint 12 de isolamento de egress foi concluída e validada pelo usuário no Docker local: tráfego público funciona pelo proxy; saída direta, destinos privados e redirects para loopback foram bloqueados; serviços reiniciaram com a política aplicada; processos da API e proxy rodam sem privilégios elevados. O gate não cobre preparação de produção/deploy público.

## Progresso Atual (Fase 1 - MVP Concluída)
- **Frontend V1 Pronto:** Interface visual totalmente funcional, integrada ao backend e lidando nativamente com estados de erro da API. Textos simulados foram permanentemente substituídos pelos dados da API (Sprint 10 concluída).
- **Backend API & Motor:** 
  - FastAPI estruturado e servindo requisições (`/api/scan`).
  - Playwright integrado operando em contexto bloqueado (otimizado).
- Validação da URL inicial e filtro de destino para requests HTTP(S) do contexto do navegador; permanece necessário isolamento de egress para cobrir redirects e DNS rebinding.
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

## Próxima etapa proposta — qualidade dos achados

A Sprint 13 está validada: o usuário confirmou “Análise híbrida” em uma análise do Mercado Livre, concluída em 13.161 ms. A API combina o Gemini com as regras determinísticas e mantém o fallback.

O teste expôs um possível falso positivo: “Pop-up / overlay intrusivo” com evidência “Pular para o conteúdo Comentar”. A regra determinística atual dispara com qualquer seletor [role=dialog], sem comprovar que o elemento é um pop-up visível. Próxima microsprint proposta: revisar a regra de overlay, testar uma página neutra e uma página com modal real, e manter evidência literal/visível para cada achado.

O arquivo MICROSPRINTS.md exige aprovação do usuário antes de avançar. Não iniciar essa microsprint, deploy ou persistência antes dessa aprovação.
 ## Próximos Desafios (Roadmap / Fases 2+)
Se houver uma próxima sessão ou retomada do desenvolvimento, os vetores de avanço seriam:
1. **Camada de Dados:** Atualmente, nada é salvo (stateless). Histórico exigirá uma microsprint de banco de dados e privacidade.
2. **Módulo de Deploy:** Planejar e validar hospedagem em VPS (Linux) em uma microsprint própria antes de expor publicamente.

## Dicas Rápidas
- *Windows Asyncio:* Nunca use `uvicorn backend.main:app` direto sem entender o impacto no loop do SO. Confie no `run_server.py`.
- *Playwright:* Não faça scraping sem acionar o `check_ssrf()`. Sempre isole as sessões do navegador (`BrowserContext`).
- *Acesso Remoto:* Lembre-se, o backend faz as requests do lugar onde ele está hospedado. Em nuvem, certifique-se que o IP tem liberação para scraping.
