# RASTRO - Decisões Técnicas

Registro das decisões de arquitetura e tecnologia tomadas até o momento. Não reabra essas discussões a menos que uma limitação grave seja encontrada.

## Stack Aprovado
- **Frontend**: HTML/CSS/JS puros baseados no protótipo existente. Estética "terminal/hacker" monoespaçada. Sem frameworks pesados no MVP.
- **Backend**: Python + FastAPI. Tipagem forte (Pydantic) e ecossistema favorável para scraping e AI.
- **Scraping**: Playwright. Ideal para lidar com SPAs, capturar DOM real após execução de JS e interceptar modais. Crawl4AI pode ser integrado posteriomente se a extração precisar de conversão para markdown limpo, mas a prioridade inicial é o Playwright básico.
- **LLM (opcional, Sprint 13)**: provedor configurável via API compatível com OpenAI e SDK Python `openai`. Gemini 3.8 Flash foi testado por chamada direta; Qwen3.8-Flash via Alibaba Cloud Model Studio/DashScope continua compatível. Configuração genérica: `LLM_ENABLED` (desativado por padrão), `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL` e `LLM_BASE_URL`; `DASHSCOPE_API_KEY` é mantida como variável legada. A análise determinística permanece ativa e é o fallback quando a IA está desativada ou indisponível. A faixa gratuita do Gemini pode usar os dados enviados para melhoria de produtos e revisão humana; não enviar conteúdo sensível.
- **Hospedagem (Futuro)**: Oracle Cloud (VPS Free Tier) com Docker.

## Decisões Arquiteturais e Restrições
- **Zero Bancos de Dados no MVP**: O scanner inicial não guardará estado. Insere URL, processa, devolve relatório e esquece.
- **Anti-SSRF em camadas**: A URL inicial é validada antes do scraping e requests HTTP(S) do contexto do navegador recebem um filtro de destino. Isso reduz exposição local, mas não garante proteção contra redirects ou DNS rebinding; isolamento de egress é requisito antes de uso público.
- **Sem Multi-Agentes de Autoria**: O desenvolvimento não usará a rede complexa de subagentes para codar de forma invisível. Tudo deve ser feito em passos curtos e mostrados ao usuário. A revisão manual é imperativa.

## Limitações Conhecidas (Decisões Pendentes)
- **Bloqueios Anti-Bot**: O MVP não tentará bypassar Cloudflare/Datadome de forma agressiva. Se a página bloquear, o erro "Página inacessível" é retornado de forma graciosa.
- **Isolamento de rede do Chromium**: A validação por aplicação não substitui firewall/proxy de egress. O servidor deve permanecer em loopback; não fazer deploy público até validar uma barreira de rede que também cubra redirects e DNS rebinding.
- **Custo e Limite de Contexto do LLM**: Nunca enviar o HTML inteiro ao provedor. A extração semântica usa no máximo 12.000 caracteres de texto visível, até 20 sinais de controles e um recorte limitado do HTML apenas para localizar esses sinais; o payload é texto estruturado limitado a 16.000 caracteres. O scraper aguarda até 1.800 ms após DOMContentLoaded por padrão (configurável até 5.000 ms) para hidratação de SPAs; a etapa LLM tem timeout padrão de 30 segundos.
- **Score combinado**: quando um LLM estiver ativo, achados determinísticos e semânticos contribuem para o mesmo score ponderado por severidade. O score continua heurístico e não é uma probabilidade calibrada; os resultados pedem revisão contextual.
