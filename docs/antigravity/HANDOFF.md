# RASTRO — Handoff de Sessão

## Resumo Executivo
O projeto RASTRO (site de verificação de dark patterns, estilo VirusTotal — sem contas, decisão do usuário em 2026-10-19) concluiu as Sprints 0–13.3 e as Microsprints 14.1–14.24 + 15.1 (histórico anônimo no servidor). O usuário confirmou a mensagem de limite para URL acima de 2.048 caracteres e os quatro casos locais de classificação lexical da 14.18. Em 2026-10-16, a imagem Docker foi reconstruída e `backend/test_rendered_evidence.py` validou os casos das microsprints 14.16–14.23 tanto no Python local quanto dentro do container `rastro-api-1`; a conferência visual em página real ficou opcional para o usuário. A categoria segura de falha do LLM ainda não foi observada em indisponibilidade real. A plataforma usa frontend Vanilla HTML/CSS/JS e backend Python (FastAPI + Playwright). O fluxo não está pronto para exposição pública.

**Checkpoint Git:** em 2026-10-16, o README reescrito foi enviado a `main` (`da5885f`) e `develop` (`13041a8`), e o estado completo do MVP foi commitado na `develop` (`d57d813`). O working tree da `main` segue com as mesmas alterações não commitadas por escolha do usuário; a `develop` preserva o histórico antigo da extensão por decisão dele.

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

A regra de urgência não usa mais a presença isolada de classe/id `timer` ou `countdown` no HTML como finding. O Playwright reúne uma lista curta apenas de elementos nomeados como contador, visíveis na viewport e com texto em formato de tempo; esse sinal pode gerar urgência alta. Evidências textuais explícitas, como “oferta termina hoje”, continuam na regra de urgência textual de severidade média. Termos isolados como “timer” e “countdown” não bastam. Em 2026-10-16, `backend/test_rendered_evidence.py` validou timer visível com valor temporal, timer oculto e timer vazio no Python local e dentro do container reconstruído.

## Microsprint 14.17 implementada — Exigir contexto para pré-seleção

A regra não analisa mais o atributo estático `checked` no HTML nem pontua checkbox sem rótulo. O Playwright observa o estado atual marcado do checkbox, seus rótulos associados e visíveis na viewport; a regra só cria achado quando o texto do rótulo corresponde ao contexto já conhecido de marketing/newsletter/oferta. Evidência curta permanece em memória e nenhuma nova categoria é enviada ou salva. Em 2026-10-16, `backend/test_rendered_evidence.py` validou os quatro cenários no Python local e dentro do container: marketing pré-marcado gera achado; comum marcado, marketing desmarcado e sem rótulo visível não geram.

## Microsprint 14.18 implementada — Separar escassez de urgência vaga

A regra de falsa escassez agora exige quantidade ou referência explícita a estoque, unidades, itens, vagas ou oferta limitada. Chamadas vagas “corra”, “hurry”, “apresse-se” e “act now” passaram para o finding de urgência textual média; “acabando” sozinho deixou de ser evidência. O usuário confirmou os quatro casos no Python local; em 2026-10-16 a imagem foi reconstruída e `backend/test_rendered_evidence.py` repetiu os casos dentro do container com os mesmos resultados.

## Microsprint 14.19 implementada — Ignorar texto de escassez não renderizado

O scraper fornece à regra de escassez somente trechos curtos de elementos efetivamente renderizados pelo navegador; conteúdo abaixo da dobra continua elegível. Elementos ocultos por estilo computado, `hidden` ou `aria-hidden` são descartados. O limite é de 500 candidatos e 200 caracteres por trecho; a evidência adicional não é enviada ao LLM nem persistida. Em 2026-10-16, `backend/test_rendered_evidence.py` validou no Python local e dentro do container: texto renderizado abaixo da dobra gera achado; `display:none`, `visibility:hidden`, `hidden`, `aria-hidden` ancestral e opacidade quase zero não geram; na mesma página a evidência cita só o trecho visível.

## Microsprint 14.20 concluída — Confirmshaming só em texto renderizado

A regra de confirmshaming não varre mais o HTML estático: ela consome a mesma lista de candidatos renderizados usada pela escassez, que passou a incluir `a` entre os elementos elegíveis e foi renomeada para `collect_rendered_text_candidates`/`rendered_text_evidence` (interno; o contrato da API não mudou). O fallback estático continua disponível para chamadas fora do fluxo com navegador.

Em 2026-10-16, `backend/test_rendered_evidence.py` validou no Python local e dentro do container reconstruído: “Não, obrigado” renderizado abaixo da dobra gera achado; `display:none`, `visibility:hidden`, `hidden` e `aria-hidden` ancestral não geram; a evidência cita só o trecho visível. Regressões `test_overlay_detection.py` e `test_scraper_routing.py` seguem passando.

## Microsprint 14.21 concluída — Ancoragem só com preço antigo renderizado

A regra de ancoragem não varre mais o HTML estático: o scraper devolve `rendered_price_evidence`, uma lista curta de elementos de preço antigo efetivamente renderizados (mesmos seletores de antes) com os blocos ancestrais compactos de até 4 níveis/180 caracteres que a regra já usava. A verificação de ocultação é a mesma das demais coletas, mas não exige posição na viewport — conteúdo abaixo da dobra segue elegível. O critério de valores distintos da 14.13 e o fallback estático fora do navegador foram preservados. O contrato da API não mudou.

Em 2026-10-16, `backend/test_rendered_evidence.py` validou no Python local e dentro do container reconstruído: `del`+preço atual abaixo da dobra gera achado; `display:none`, `visibility:hidden`, `aria-hidden` ancestral e `del` oculto com preço visível não geram; `R$ 79,99` repetido continua sem achado. Com isso, as 7 regras determinísticas consomem somente sinais confirmados como renderizados pelo navegador.

## Microsprint 14.22 concluída — Texto estacionado fora da tela não pontua

Elementos posicionados inteiramente em espaço negativo (`position:absolute; left:-9999px`, `top:-9999px`) têm geometria e `innerText`, mas o usuário nunca os vê. As coletas de candidatos de texto e de contexto de preço agora descartam elementos com `rect.right <= 0` ou `rect.bottom <= 0`. Conteúdo abaixo da dobra mantém limites positivos e continua elegível; parcialmente fora da tela também. As coletas que já exigem interseção com a viewport (timer, checkbox, overlay, consentimento) não mudaram.

Em 2026-10-16, `backend/test_rendered_evidence.py` validou no Python local e dentro do container reconstruído: escassez à esquerda/acima da tela, recusa fora da tela e bloco de preço antigo fora da tela não geram achado; elemento parcialmente visível continua elegível.

## Microsprint 14.23 concluída — Urgência textual só em texto renderizado

A variante textual de urgência avaliava o `body.innerText` completo, que inclui texto fora da tela e oculto por CSS. No fluxo com navegador, a regra passa a avaliar `rendered_text_candidates` — a mesma lista de escassez e confirmshaming. O sinal alto de timer visível e o fallback estático fora do navegador foram preservados; o contrato não mudou. Com isso, todo achado textual exige elemento renderizado.

Em 2026-10-16, `backend/test_rendered_evidence.py` validou no Python local e dentro do container reconstruído: “Corra!” fora da tela e oculto não geram achado; “Corra para aproveitar!” renderizado segue gerando urgência média; os casos de timer da 14.16 passam.

## Microsprint 14.24 concluída — Contrato reconciliado com as regras renderizadas

`docs/api-contract.md` (v0.3) ainda descrevia apenas a coleta renderizada da escassez e omitia confirmshaming, urgência textual e ancoragem baseadas em evidência renderizada, além da exclusão de texto estacionado fora da tela. O contrato foi atualizado para v0.4 e o comentário do schema `Finding.engine` deixou de listar o valor `stub` inexistente — só `deterministic` e `llm` são emitidos.

Em 2026-10-19, `backend/test_rendered_evidence.py` (24/24) e `backend/test_ssrf.py` (30/30) passaram no Python local; não houve mudança funcional a validar no container.

## Microsprint 15.1 concluída — Histórico anônimo no servidor (modelo A)

Decisão do usuário: o RASTRO é um site de verificação pontual estilo VirusTotal — "verificar e só", sem contas. O modelo B (contas/e-mail) da proposta `PERSISTENCIA.md` foi descartado.

Implementado: cookie opaco `rastro_hid` (HttpOnly, SameSite=Lax, 1 ano); `backend/db.py` com SQLite em `RASTRO_DB_PATH`; auto-save do resumo a cada `/api/scan`; `GET /api/history`, `DELETE /api/history/{id}` e `DELETE /api/history` escopados à identidade; retenção de 100 itens; gravação best-effort. URL completa, HTML e texto integral continuam fora do banco. No Compose, volume `api-data` montado em `/data` (criado no Dockerfile com dono `pwuser`). O frontend lista o histórico do servidor e perdeu o botão "SALVAR NO HISTÓRICO" (auto-save); o `localStorage` antigo fica órfão e não é migrado. Contrato v0.5.

`backend/test_history.py` (18/18) passou no Python local e dentro do container `rastro-api-1` reconstruído; sintaxe do frontend conferida com `node --check`; suites anteriores seguem verdes. Persistência confirmada ponta a ponta: item inserido no volume `api-data` continuou listado após `docker compose restart api` e foi removido por `DELETE /api/history` (204). Nota operacional: `docker compose exec` roda como root e, por `cap_drop: ALL`, não escreve em `/data` — usar `--user pwuser` para probes. A conferência visual do histórico na interface fica para o usuário.

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
2. **Camada de Dados remota:** contas e histórico sincronizado exigirão banco e microsprint de privacidade própria. Proposta de escopo pronta em `docs/antigravity/PERSISTENCIA.md` (decisão pendente: histórico anônimo × contas); aguarda aprovação para implementar.
3. **Módulo de Deploy:** Planejar e validar hospedagem em VPS (Linux) em uma microsprint própria antes de expor publicamente. Proposta de escopo pronta em `docs/antigravity/DEPLOY.md` (rate limit + cookie `Secure` como pré-requisitos); aguarda autorização.

## Dicas Rápidas
- *Windows Asyncio:* Nunca use `uvicorn backend.main:app` direto sem entender o impacto no loop do SO. Confie no `run_server.py`.
- *Playwright:* Não faça scraping sem acionar o `check_ssrf()`. Sempre isole as sessões do navegador (`BrowserContext`).
- *Acesso Remoto:* Lembre-se, o backend faz as requests do lugar onde ele está hospedado. Em nuvem, certifique-se que o IP tem liberação para scraping.
