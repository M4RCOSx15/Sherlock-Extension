# RASTRO — Handoff de Sessão

## Resumo Executivo
O projeto do SaaS RASTRO (Auditor de Dark Patterns Web) concluiu as Sprints 0–13.3 e implementou as Microsprints 14.1–14.19. O usuário confirmou a mensagem de limite para URL acima de 2.048 caracteres e os quatro casos locais de classificação lexical da 14.18. As microsprints 14.16–14.19 aguardam validação integrada no Docker; o container reportado pelo usuário tinha 8 horas e não confirma rebuild do código atual. A categoria segura de falha do LLM ainda não foi observada em indisponibilidade real. A plataforma usa frontend Vanilla HTML/CSS/JS e backend Python (FastAPI + Playwright). O fluxo não está pronto para exposição pública.

**Checkpoint Git pendente:** nenhuma alteração desta sequência foi commitada ou enviada. O ambiente bloqueou escrita em `.git` e não encontrou credenciais GitHub; as alterações continuam no working tree.

O sistema recebe uma URL pela interface, carrega a página com Playwright, filtra requests por destino e aplica regras determinísticas ao DOM. A Sprint 12 de isolamento de egress foi concluída e validada pelo usuário no Docker local: tráfego público funciona pelo proxy; saída direta, destinos privados e redirects para loopback foram bloqueados; serviços reiniciaram com a política aplicada; processos da API e proxy rodam sem privilégios elevados. O gate não cobre preparação de produção/deploy público.

## Progresso Atual (Fase 1 - MVP Concluída)
- **Frontend V1 Pronto:** Interface visual totalmente funcional, integrada ao backend e lidando nativamente com estados de erro da API. Textos simulados foram permanentemente substituídos pelos dados da API (Sprint 10 concluída).
- **Backend API & Motor:** 
  - FastAPI estruturado e servindo requisições (`/api/scan`).
  - Playwright integrado operando em contexto bloqueado (otimizado).
- Validação da URL inicial e filtro de destino para requests HTTP(S) do contexto do navegador; permanece necessário isolamento de egress para cobrir redirects e DNS rebinding.
  - Motor analítico em `analyzer.py` executando pontuação com pesos e regras estruturadas em CSS/Regex.
- **Ambiente Resolvido:** Problemas crônicos do ecossistema Windows (Playwright vs. Uvicorn Asyncio loops) foram pacificados pela criação do arquivo `run_server.py`.

## Como Rodar Localmente com Docker (recomendado)
Inicie o Docker Desktop, espere o mecanismo ficar pronto e, em um PowerShell na raiz do projeto (`dark-plugin`), rode:
```powershell
docker compose up -d --build api
docker compose ps
curl.exe -sS http://127.0.0.1:8000/api/health
```
O Compose inicia também `egress-proxy`; espere ambos os serviços ficarem `healthy`. `health: starting` pode aparecer brevemente durante a inicialização.

* **Aplicação Web:** `http://127.0.0.1:8000/`
* **Swagger API:** `http://127.0.0.1:8000/docs`
* **Health check:** `http://127.0.0.1:8000/api/health`

Para consultar logs: `docker compose logs --tail=100 api` ou `docker compose logs --tail=100 egress-proxy`. Use `docker compose restart` para reiniciar sem rebuild, `docker compose up -d --build api` para reconstruir após alterações e `docker compose down` para parar/remover containers e rede. Se houver erro de conexão com `dockerDesktopLinuxEngine`, abra o Docker Desktop e aguarde a inicialização. O ambiente `.venv` não controla o Docker.

A alternativa Python (`.venv\Scripts\activate` e `python run_server.py`) é para desenvolvimento local e não recebe o isolamento de egress do Compose. Consulte o `README.md` para os passos de instalação.

## Microsprint 14.1 concluída — Histórico local

O frontend salva um resumo somente depois do clique em “SALVAR NO HISTÓRICO”. O armazenamento usa `localStorage`, é limitado a 10 itens e não inclui URL completa, caminho, query, fragmento ou HTML. O resumo mostra domínio, data, score, risco e trechos limitados de evidência. A interface permite abrir a lista, remover um item ou apagar tudo.

A implementação está no frontend e não altera API, scraper nem Docker. Em 2026-09-28, o usuário confirmou que salvar e remover relatórios funcionaram.

## Microsprint 14.2 concluída — Exportação Markdown

O resultado atual e os itens salvos oferecem download local `.md`. O arquivo contém domínio, data, score heurístico, risco e evidências curtas; não inclui URL completa, HTML ou segredo. Texto de evidência é escapado para Markdown. A implementação não altera API, scraper ou Docker.

Em 2026-09-28, o usuário confirmou que o download funcionou. A revisão manual do conteúdo do arquivo não foi relatada separadamente. Nenhum teste automatizado foi executado nesta sessão.

## Microsprint 14.3 concluída — Transparência sobre dados enviados ao modelo

Antes do botão de análise, a interface informa que o RASTRO acessa a URL e, se a etapa semântica estiver ativa, envia texto limitado e sinais dos controles da página ao provedor configurado (atualmente Gemini). O texto esclarece que o HTML integral não é enviado e que as regras determinísticas continuam disponíveis. O aviso estático é separado do status dinâmico da análise. API e contrato não foram alterados.

O usuário autorizou seguir após receber a atualização. Nenhum teste automatizado foi executado nesta sessão.

## Microsprint 14.4 concluída — Explicação do score

O resultado tem uma seção expansível que explica a soma por severidade (5/10/20/30 pontos), o limite de 100, as faixas de risco e que o “%” não representa probabilidade de manipulação. O Markdown atual e histórico inclui a mesma explicação. O algoritmo, API e esquema local permanecem intactos.

O usuário autorizou seguir após a entrega. Nenhum teste automatizado foi executado nesta sessão.

## Microsprint 14.5 concluída — Gravidade e origem dos achados

Os cartões mostram severidade traduzida e origem (`regra determinística`, `análise semântica (IA)` ou origem não informada). O histórico armazena gravidade e motor, mantendo compatibilidade com entradas antigas; o Markdown inclui ambos em cada achado.

O usuário autorizou seguir após a entrega. Nenhum teste automatizado foi executado nesta sessão.

## Microsprint 14.6 concluída — Contexto por achado

Os achados têm explicação recolhível específica para cada categoria conhecida, incluindo o sinal observado e o que conferir na página. A exportação Markdown traz essa orientação. O ID da categoria fica no resumo local para recuperar a orientação; registros antigos e IDs desconhecidos usam texto genérico. Nenhuma regra ou score foi alterado.

Em 2026-09-28, o usuário confirmou que a explicação e o Markdown funcionaram. Nenhum teste automatizado foi executado nesta sessão.

## Microsprint 14.7 concluída — Metadados da execução

O histórico local e Markdown preservam método (`determinístico` ou `híbrido`), status da etapa semântica, categoria segura de falha se houver, duração, total de elementos do DOM e número de regras aplicadas. Registros antigos continuam válidos e mostram esses itens como não registrados. Não se armazena URL completa, texto da página, resposta bruta ou segredo.

Em 2026-09-28, o usuário confirmou que os recursos/metadados funcionaram e autorizou seguir. Nenhum teste automatizado foi executado nesta microsprint.

## Microsprint 14.8 concluída — Runbook Docker-first e documentação

README, estado e handoff agora descrevem Docker Compose como o modo recomendado, com o pré-requisito Docker Desktop, health check real `/api/health`, interface, Swagger, logs, restart, rebuild e parada. Python direto permanece como alternativa sem isolamento de egress. A documentação registra que o Gemini híbrido foi confirmado no Docker e diferencia histórico/download locais do navegador de persistência/endpoints da API.

A microsprint não modificou código funcional, containers ou configuração. O usuário confirmou que a documentação está correta. Nenhum comando Docker foi executado na máquina do usuário nem teste de aplicação foi executado nesta microsprint.

## Microsprint 14.9 concluída — Referência da evidência no DOM

`backend/analyzer.py` procura trechos curtos entre aspas na evidência e, se os encontrar no HTML capturado, gera caminho CSS posicional composto só por nomes de tags e `nth-of-type`. `backend/main.py` expõe o caminho em `findings[].dom_reference`; evidências sem correspondência retornam `null`. O frontend valida o formato antes de exibi-lo em detalhes recolhíveis nos achados, no histórico local e no relatório Markdown.

O caminho pertence à captura analisada e pode mudar se a página mudar. Ele não contém atributos/texto da página, não comprova visibilidade e não valida a interpretação do achado. O contrato da API documenta o campo opcional e esses limites. `git diff --check` passou; o usuário confirmou que estava correto e autorizou a próxima microsprint.

## Microsprint 14.10 concluída — Domínio final nos relatórios

O resultado já usa `apiData.domain`, preenchido pelo backend com o host de `page_data.final_url` após redirects. `createReportSnapshot` agora também prioriza esse campo, com fallback ao hostname digitado para respostas antigas; assim histórico local e Markdown identificam a página efetivamente analisada. O contrato diferencia a URL solicitada (`url`) do domínio final (`domain`). O arquivo completo continua omitido do histórico e dos downloads.

O usuário reconstruiu e analisou um endereço redirecionado, confirmando que `example.com` apareceu como domínio analisado. A conferência separada no histórico e no Markdown não foi relatada; ambos recebem o mesmo `domain` do snapshot. Nenhum teste automatizado foi executado.

## Microsprint 14.11 concluída — Explicar redirecionamentos entre domínios

O resultado e relatórios agora recebem `requestedDomain` do hostname submetido, além de `domain` (final analisado). A tela, o histórico e o Markdown mostram uma nota apenas quando os domínios diferem, ignorando diferenças de caixa e prefixo `www.`. Compatibilidade com registros antigos preserva `requestedDomain: null`; nenhum aviso aparece neles. Só hostnames são armazenados/exportados, sem URL completa, caminho ou query.

Em 2026-09-28, o usuário confirmou que o aviso de redirecionamento funcionou. Nenhum teste automatizado foi executado. A validação separada do histórico e do Markdown não foi relatada; ambos usam os mesmos hostnames do resultado.

## Microsprint 14.12 concluída — Esperar a estabilização do DOM com limite

`backend/scraper.py` substitui a pausa fixa por uma assinatura compacta do texto visível e da quantidade de elementos, consultada a cada 250 ms. A espera tem mínimo de 2.000 ms, exige 750 ms sem mudanças antes de encerrar e respeita `SCRAPER_RENDER_WAIT_MS` (padrão 3.500 ms, limitado a 0–5.000 ms). Não usa `networkidle`. Se a navegação mudar durante a janela, o destino final é validado novamente contra SSRF antes da extração.

O `.env` local teve somente `SCRAPER_RENDER_WAIT_MS` ajustado para 3.500; os demais valores não foram lidos nem alterados. Documentação, `.env.example` e fallback do Compose refletem o padrão. O usuário confirmou que conferiu a espera adaptativa, sem registrar valores de duração ou quantidade de elementos. Nenhum teste automatizado foi executado.

## Microsprint 14.13 concluída — Exigir preços distintos para sinalizar ancoragem

`backend/analyzer.py` agora normaliza quantias monetárias e só sinaliza ancoragem quando encontra valores distintos na mesma moeda em um bloco curto associado a um seletor de preço antigo/riscado. Repetições do mesmo valor não bastam; a evidência continua sendo o texto literal do bloco e a regra limita a um finding por página.

Em 2026-09-28, o usuário autorizou o avanço após a implementação. Não informou separadamente os resultados dos dois casos de preço. Revisão estática e `git diff --check` passaram; nenhum teste automatizado ou comando Docker foi executado.

## Microsprint 14.14 concluída — Exibir o volume de texto visível capturado

A API agora retorna `meta.visible_text_characters`, a quantidade de caracteres do texto visível capturado. A interface acrescenta o número ao resumo do resultado; histórico local e Markdown armazenam/exportam somente essa contagem. A documentação esclarece que é o volume total extraído, não o texto enviado ao LLM, que continua limitado separadamente.

Relatórios antigos normalizam o campo ausente como não registrado. Em 2026-09-28, o usuário mostrou 12.097 caracteres no resultado e no histórico; itens antigos sem a métrica continuam exibindo “texto visível não registrado”. O usuário confirmou que o Markdown contém `12097` e só a contagem, sem o texto da página. A análise do OLX.com.br exibiu 3.152 elementos e um finding de preço; o Gemini atingiu o limite de uso e o fallback determinístico concluiu. Validação manual concluída; nenhum teste automatizado foi executado.

## Microsprint 14.15 concluída — Limitar o tamanho da URL submetida

O backend rejeita URLs acima de 2.048 caracteres depois de remover espaços nas pontas e também confere o tamanho após acrescentar `https://` quando falta esquema. A interface aplica o mesmo limite e mostra os erros `422` de validação da API junto ao campo. Em 2026-09-29, o usuário confirmou a mensagem “A URL deve ter no máximo 2.048 caracteres.” Uma URL pública normal não foi repetida durante esta validação, mas o fluxo correspondente não foi alterado. Nenhum teste automatizado nem comando Docker foi executado nesta microsprint.

## Microsprint 14.16 implementada — Exigir evidência visível para timer

A regra de urgência não usa mais a presença isolada de classe/id `timer` ou `countdown` no HTML como finding. O Playwright reúne uma lista curta apenas de elementos nomeados como contador, visíveis na viewport e com texto em formato de tempo; esse sinal pode gerar urgência alta. Evidências textuais explícitas, como “oferta termina hoje”, continuam na regra de urgência textual de severidade média. Termos isolados como “timer” e “countdown” não bastam. A pedido do usuário, avançamos antes de validação manual; conferir timer visível e timer oculto/vazio permanece pendente. Nenhum teste automatizado nem comando Docker foi executado nesta microsprint.

## Microsprint 14.17 implementada — Exigir contexto para pré-seleção

A regra não analisa mais o atributo estático `checked` no HTML nem pontua checkbox sem rótulo. O Playwright observa o estado atual marcado do checkbox, seus rótulos associados e visíveis na viewport; a regra só cria achado quando o texto do rótulo corresponde ao contexto já conhecido de marketing/newsletter/oferta. Evidência curta permanece em memória e nenhuma nova categoria é enviada ou salva. Falta reconstruir e validar checkbox de marketing pré-marcado, checkbox comum marcado e controle sem rótulo visível. Nenhum teste automatizado nem comando Docker foi executado nesta microsprint.

## Microsprint 14.18 implementada — Separar escassez de urgência vaga

A regra de falsa escassez agora exige quantidade ou referência explícita a estoque, unidades, itens, vagas ou oferta limitada. Chamadas vagas “corra”, “hurry”, “apresse-se” e “act now” passaram para o finding de urgência textual média; “acabando” sozinho deixou de ser evidência. Docker não estava acessível neste ambiente (`permission denied` no named pipe `docker_engine`), então o rebuild e a conferência manual estão pendentes. Nenhum teste automatizado foi executado.

## Microsprint 14.19 implementada — Ignorar texto de escassez não renderizado

O scraper fornece à regra de escassez somente trechos curtos de elementos efetivamente renderizados pelo navegador; conteúdo abaixo da dobra continua elegível. Elementos ocultos por estilo computado, `hidden` ou `aria-hidden` são descartados. O limite é de 500 candidatos e 200 caracteres por trecho; a evidência adicional não é enviada ao LLM nem persistida. O rebuild e a comparação de texto visível versus oculto ainda precisam ser confirmados no Docker. Nenhum teste automatizado foi executado.

## Microsprint 13.2 concluída — assimetria em consentimento

O usuário aprovou a Microsprint 13.2 após a validação da 13.1. O objetivo é não pontuar a mera presença de banner de cookies e produzir apenas um sinal baixo quando aceitar e recusar estiverem ausentes ou visivelmente desequilibrados na camada inicial.

Na validação da microsprint 13.1, os casos de página neutra, dialog não modal, modal visível e modal oculto passaram. A análise do Mercado Livre no Docker retornou 1.624 elementos, score de 10% e evidência do banner visível; o texto “Pular para o conteúdo” não voltou a ser reportado.

O scraper extrai rótulos e sinais visuais básicos dos controles de consentimento; `backend/analyzer.py` compara aceitar, recusar e configurar e emite `consent_asymmetry` com severidade baixa. `python backend/test_overlay_detection.py` passou nos seis cenários de regressão. Os containers Docker ficaram saudáveis após a reconstrução. Na análise do Mercado Livre, o usuário observou 1.624 elementos, score de 5% e apenas o sinal de assimetria; o finding genérico de overlay deixou de aparecer. O Gemini ficou indisponível nessa requisição, então o fallback determinístico concluiu a análise.

O resultado é heurístico: não prova intenção manipulativa nem faz avaliação jurídica.

Microsprint 13.2 validada e concluída em 2026-09-28. A Microsprint 13.3 está implementada; a categoria segura ainda aguarda uma falha natural do provedor para validação visual. Não provocar indisponibilidade alterando a chave.

## Microsprint 13.3 concluída — diagnóstico seguro do LLM

Motivo: a última análise do Mercado Livre não conseguiu usar o Gemini e retornou o resultado determinístico; a integração híbrida havia funcionado anteriormente. A implementação atual acrescenta `LLMAnalysis.unavailable_reason`, categoriza falhas de timeout, rede, limite, autenticação, configuração, resposta inválida e provedor, e expõe somente a categoria segura no novo campo `meta.llm_unavailable_reason`. A interface traduz a categoria em texto curto. O corpo do erro, conteúdo da página, URL, chave e request ID permanecem fora da resposta pública. A política atual de retries/timeout permanece igual.

Revisão manual do diff e `git diff --check` concluídos. O usuário reconstruiu a API no Docker; a última análise híbrida do Mercado Livre passou com 1.625 elementos e os logs não mostraram `LLM analysis unavailable`. O caminho de sucesso está confirmado, mas ainda não houve falha real para confirmar a categoria `meta.llm_unavailable_reason`. Não alterar a chave nem a configuração válida para forçar uma falha.
## Próximos Desafios (Roadmap / Fases 2+)
Se houver uma próxima sessão ou retomada do desenvolvimento, os vetores de avanço seriam:
1. **Histórico e exportação locais**: usam `localStorage` e download Markdown; não sincronizam entre dispositivos.
2. **Camada de Dados remota:** contas e histórico sincronizado exigirão banco e microsprint de privacidade própria.
3. **Módulo de Deploy:** Planejar e validar hospedagem em VPS (Linux) em uma microsprint própria antes de expor publicamente.

## Dicas Rápidas
- *Windows Asyncio:* Nunca use `uvicorn backend.main:app` direto sem entender o impacto no loop do SO. Confie no `run_server.py`.
- *Playwright:* Não faça scraping sem acionar o `check_ssrf()`. Sempre isole as sessões do navegador (`BrowserContext`).
- *Acesso Remoto:* Lembre-se, o backend faz as requests do lugar onde ele está hospedado. Em nuvem, certifique-se que o IP tem liberação para scraping.
