# RASTRO - Decisões Técnicas

Registro das decisões de arquitetura e tecnologia tomadas até o momento. Não reabra essas discussões a menos que uma limitação grave seja encontrada.

## Stack Aprovado
- **Frontend**: HTML/CSS/JS puros baseados no protótipo existente. Estética "terminal/hacker" monoespaçada. Sem frameworks pesados no MVP.
- **Backend**: Python + FastAPI. Tipagem forte (Pydantic) e ecossistema favorável para scraping e AI.
- **Scraping**: Playwright. Ideal para lidar com SPAs, capturar DOM real após execução de JS e interceptar modais. Crawl4AI pode ser integrado posteriomente se a extração precisar de conversão para markdown limpo, mas a prioridade inicial é o Playwright básico.
- **LLM (Fase 2 apenas)**: Gemini Flash via AI Studio ou Qwen via OpenRouter. A Fase 1 será 100% determinística (sem uso de LLM).
- **Hospedagem (Futuro)**: Oracle Cloud (VPS Free Tier) com Docker.

## Decisões Arquiteturais e Restrições
- **Zero Bancos de Dados no MVP**: O scanner inicial não guardará estado. Insere URL, processa, devolve relatório e esquece.
- **Anti-SSRF rigoroso**: O backend de scraping nunca poderá acessar IPs da rede local/interna. A sanitização de URL é bloqueante (Sprint 7).
- **Sem Multi-Agentes de Autoria**: O desenvolvimento não usará a rede complexa de subagentes para codar de forma invisível. Tudo deve ser feito em passos curtos e mostrados ao usuário. A revisão manual é imperativa.

## Limitações Conhecidas (Decisões Pendentes)
- **Bloqueios Anti-Bot**: O MVP não tentará bypassar Cloudflare/Datadome de forma agressiva. Se a página bloquear, o erro "Página inacessível" é retornado de forma graciosa.
- **Custo e Limite de Contexto do LLM**: A extração de dados do Playwright precisa ser enxuta. Jogar o HTML inteiro da página para o LLM na Fase 2 inviabilizaria os custos ou os limites de token. Teremos que filtrar o DOM drasticamente antes de enviá-lo ao prompt (apenas textos de botões, banners, labels e popups).
