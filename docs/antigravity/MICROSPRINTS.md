# RASTRO - Planejamento em Microsprints

O projeto será desenvolvido etapa por etapa (microsprints). O agente não pode avançar para a próxima sprint sem a aprovação do usuário na atual.

## Fase: Fundação e Protótipo (Sem Backend Funcional)

### [x] Sprint 0 — Reconhecimento e plano, sem código
- **Escopo**: Fazer o agente entender o estado real do projeto lendo `STATE.md`, as regras e inspecionando os arquivos em `prototype/`.
- **Critério de Aceite**: O agente entrega um resumo do que entendeu e lista o plano, sem tocar em nenhuma linha de código da aplicação.

### [x] Sprint 1 — Fundação e proteção do repositório
- **Escopo**: Organizar estrutura de pastas. Criar/atualizar `.gitignore` para barrar segredos. Criar `.env.example`.
- **Critério de Aceite**: Arquivos ignorados pelo Git corretamente. Nenhum segredo mockado. Ambiente base documentado.

### [x] Sprint 2 — Inventário visual e direção aprovada
- **Escopo**: Inspecionar o HTML/CSS do `prototype/` (estética terminal/hacker). Apontar pequenos ajustes de UI, responsividade e acessibilidade.
- **Critério de Aceite**: O agente sugere uma lista de ajustes de frontend e **aguarda aprovação** antes de codificá-los.

### [x] Sprint 3 — Polimento visual do protótipo
- **Escopo**: Aplicar os ajustes aprovados na Sprint 2. Preservar o design estático de "arte ASCII" do olho e os campos existentes.
- **Critério de Aceite**: Interface rodando localmente sem quebras visuais em desktop/mobile.

### [x] Sprint 4 — Fluxo de interface com simulação explícita (Mocks)
- **Escopo**: Adicionar JS no front para simular os estados (URL inválida, analisando, falha, sucesso com dados falsos). Botão de enviar bloqueado durante análise.
- **Critério de Aceite**: A interface tem feedback interativo sem depender de backend real.

---

## Fase: Backend e Lógica

### [x] Sprint 5 — Contrato da API, sem scraper
- **Escopo**: Definir o formato JSON para os requests/responses (como `POST /api/scan`). Tratar os cenários de erro e sucesso esperados.
- **Critério de Aceite**: Contrato documentado e validado. Frontend preparado para lidar com ele (ainda mockado).

### [x] Sprint 6 — Backend mínimo (FastAPI)
- **Escopo**: Subir uma API FastAPI básica (Hello World e `GET /api/health`).
- **Critério de Aceite**: O endpoint responde localmente e a documentação do Swagger UI (FastAPI) está acessível.

### [x] Sprint 7 — Barreira de URL e proteção contra SSRF
- **Escopo**: Impedir chamadas a IPs locais/privados (`127.0.0.1`, `10.x`, etc.) e verificar URLs maliciosas. 
- **Critério de Aceite**: Testes automatizados na API bloqueiam acessos à intranet e requisições HTTP inválidas.

### [x] Sprint 8 — Worker Playwright isolado
- **Escopo**: Instalar Playwright no backend. Configurar para abrir uma página em contexto limpo (sem cookies de sessão), fazer scraping básico do DOM e fechar. Limite de 1 análise simultânea.
- **Critério de Aceite**: Consegue extrair o `<title>` e tags `<a>` de um site de teste com segurança e sem vazamento de memória.

### [x] Sprint 9 — Regra Fase 1: Análise Determinística (Escassez/Urgência)
- **Escopo**: Implementar lógica via Regex/CSS para detectar gatilhos básicos ("Só restam X"). 
- **Critério de Aceite**: O backend recebe a URL, extrai o texto e retorna o array de `findings` se a regra determinística disparar, ou vazio caso contrário. Sem uso de LLM.

### [x] Sprint 10 — Conectar a interface à API real
- **Escopo**: Trocar os mocks do frontend pelo `fetch` real batendo no backend rodando via Playwright.
- **Critério de Aceite**: O fluxo completo (inserir URL -> esperar -> ver resultado) funciona ponta a ponta na máquina local.

### [x] Sprint 11 — Segurança da fronteira de confiança (local)
- **Escopo**: Renderizar evidências do site como texto inerte; filtrar requests HTTP(S) do Chromium contra destinos não públicos; desabilitar service workers; limitar o servidor de desenvolvimento a `127.0.0.1`; registrar as limitações de rede que ainda impedem deploy público.
- **Critério de Aceite**: Evidências contendo markup não criam elementos executáveis; casos locais de loopback, rede privada, IPv6 loopback e protocolo não HTTP são bloqueados pelo filtro; requests públicos de teste passam sem serem enviados; o servidor não escuta em todas as interfaces.
- **Limitação**: O filtro de aplicação não é uma barreira completa contra redirects ou DNS rebinding. Deploy público depende de isolamento de egress na rede/ambiente do Chromium.

### [x] Sprint 12 — Isolamento de egress do Chromium
- **Estado**: gate concluído e validado pelo usuário no Docker local em 2026-09-26. Scans públicos em example.com/YouTube passam; tentativa de egress direto para 1.1.1.1:443 retorna `BLOQUEADO`, inclusive após reinício; loopback, RFC1918 (10.0.0.1), link-local/metadata (169.254.169.254), hostname Docker interno e IPv4 mapeado em IPv6 são recusados. Redirect de controle para example.com conclui; redirect para 127.0.0.1 retorna `ACCESS_BLOCKED` sem relatório. Após `docker compose restart`, ambos os serviços retornam `healthy` e a análise pública continua funcionando. `docker compose top` confirma Uvicorn UID 1000 (`pwuser`) e Squid usuário `proxy` (UID 13); o scraper usa `chromium_sandbox=True` com seccomp customizado, sem `--no-sandbox`.
- **Escopo**: executar API e Chromium em container sem saída direta; permitir tráfego web somente por proxy dedicado; aplicar firewall de saída no scanner e no proxy; bloquear destinos privados/reservados e todo IPv6 no proxy; manter a porta da API publicada apenas em loopback; falhar fechado quando proxy obrigatório estiver ausente.
- **Arquivos**: `Dockerfile`, `compose.yaml`, `.dockerignore`, `docker/api-entrypoint.sh`, `docker/egress/` e configuração de produção do scraper.
- **Critérios para concluir**: `docker compose config` válido; imagens iniciam com usuários não privilegiados após aplicar firewall; UI/API funcionam; acesso público funciona através do proxy; destinos loopback, RFC1918, link-local/metadata, hostname interno e redirects para esses destinos são bloqueados; conexão direta de saída da API falha; Chromium mantém sandbox ativo; reiniciar containers conserva a política.
- **Gate**: concluído no Docker Engine local. Isso valida o isolamento da stack de desenvolvimento; qualquer deploy público exige uma microsprint de produção própria e aprovação explícita do usuário.

### [x] Sprint 13 — Integração opcional de LLM (Gemini/Qwen)
- **Estado**: concluída e validada no Docker local. Em 2026-09-26, o usuário confirmou na interface uma análise híbrida com Gemini 3.8 Flash em mercadolivre.com.br (13.161 ms). As regras determinísticas continuam como fallback. A validação revelou um possível falso positivo de overlay: a evidência exibida foi texto de navegação acessível (“Pular para o conteúdo”), registrado para a próxima microsprint de qualidade.
- **Escopo**: complementar as regras determinísticas com uma chamada semântica opcional a um provedor compatível com OpenAI; enviar apenas um recorte limitado de texto visível e controles da página; validar a evidência devolvida; manter a chave no backend e usar o proxy de egress existente no Docker. O adaptador Gemini usa JSON mode e omite `temperature`, que não é aceito pelo modelo configurado.
- **Fora do escopo**: streaming de raciocínio, envio do HTML integral, armazenamento da chave no repositório, treinamento/calibração estatística do score, deploy e persistência. A interface/documentação deve informar que o recorte textual é enviado ao provedor quando a opção for habilitada.
- **Critérios para concluir**: com `LLM_ENABLED=false` ou sem uma chave válida, o comportamento determinístico continua disponível; com Gemini configurado localmente, a API chama o provedor através do proxy, agrega apenas achados com citação presente no texto enviado e informa o estado em `meta.llm_status`; falha/timeout do provedor retorna o resultado determinístico; o segredo não aparece no frontend, nos relatórios ou nos logs; o `.env` não é versionado. A configuração gratuita do Gemini informa o uso dos dados enviados para melhoria de produtos e revisão humana.

### [x] Microsprint 13.1 — Reduzir falso positivo de overlay
- **Estado**: concluída em 2026-09-28. A regra não usa mais `[role=dialog]` isoladamente. O scraper verifica visibilidade efetiva na viewport e requer semântica modal ou sinais combinados de posição, z-index e área ocupada; somente então fornece texto literal como evidência.
- **Validação**: o usuário executou `python backend/test_overlay_detection.py`; passaram página neutra com link fora da tela e dialog não modal, modal visível e modal oculto. Após reconstruir a API no Docker, analisou o Mercado Livre: 1.624 elementos, score de 10% e evidência do banner de cookies visível; o texto de navegação acessível observado antes deixou de aparecer.
- **Limite**: visibilidade e forma de modal não provam intenção manipulativa. O resultado continua sendo um sinal heurístico para revisão, não uma acusação de dark pattern.

### [x] Microsprint 13.2 — Avaliar assimetria em consentimento (concluída em 2026-09-28)
- **Escopo aprovado**: distinguir presença de banner de cookies de sinais observáveis de escolha assimétrica.
- **Implementação**: extrair rótulos de ações e sinais básicos de destaque visual apenas dos controles visíveis na camada de consentimento. A regra `consent_asymmetry` usa severidade baixa para falta de recusa direta ou destaque muito maior para aceitar; presença do banner, sozinha, não cria finding. `meta.rules_applied` passa a ser 7.
- **Critérios de aceite**: banner equilibrado sem finding nem pontos; opção aceitar sem recusa direta produz evidência textual e sinal baixo; aceitar visualmente muito mais proeminente que recusar produz sinal; modal não relacionado a consentimento mantém sua detecção anterior.
- **Validação**: `python backend/test_overlay_detection.py` passou nos seis cenários: página neutra/dialog não modal, modal visível, modal oculto, banner equilibrado sem pontos, ausência de recusa direta com sinal leve e diferença de destaque entre aceitar e rejeitar. O usuário confirmou os containers `rastro-api` e `rastro-egress-proxy` como saudáveis após a reconstrução.
- **Validação integrada**: no Mercado Livre, o usuário observou 1.624 elementos, 5% de risco contextual baixo e um único finding `consent_asymmetry` (“Aceitar cookies” visível; “Configurar cookies” pode abrir outras opções). O finding anterior de overlay não aparece; a queda de 10% para 5% confirma que a presença do banner deixou de pontuar separadamente. O Gemini ficou indisponível nessa requisição e o fallback determinístico concluiu a análise.
- **Limite**: o finding é heurístico e não prova intenção manipulativa ou descumprimento legal.

### [x] Microsprint 13.3 — Diagnóstico seguro da disponibilidade do LLM
- **Motivo**: análises recentes concluíram pelo fallback determinístico quando o Gemini ficou indisponível, embora a integração híbrida já tenha funcionado anteriormente. O usuário precisa distinguir falha de configuração, timeout, limite, autenticação, conexão ou erro do provedor sem revelar detalhes sensíveis.
- **Escopo aprovado**: classificar falhas em categorias estáveis no backend; expor a categoria em `meta.llm_unavailable_reason`; traduzir a categoria em mensagem curta e compreensível na interface. Preservar o fallback determinístico e não incluir resposta bruta do provedor, prompt, URL, texto da página, chave ou request ID na resposta pública. Manter a política de retries e o limite de tempo atuais nesta microsprint.
- **Critérios de aceite**: sucesso/desativado/sem texto mantêm motivo `null`; falhas mapeiam para categorias seguras (`not_configured`, `configuration_error`, `timeout`, `rate_limited`, `authentication_error`, `network_error`, `request_rejected`, `invalid_response`, `provider_error`); interface explica a categoria sem interromper o resultado determinístico; logs continuam sem conteúdo da página ou segredo.
- **Estado**: implementação e revisão do contrato concluídas. A interface apresenta a categoria segura quando o provedor falha, mantendo o resultado determinístico. A análise híbrida após a reconstrução confirmou que o caminho de sucesso permanece funcional.
- **Limitação de validação**: não houve indisponibilidade real após a mudança para confirmar visualmente `llm_unavailable_reason`. Não alterar a chave nem quebrar a configuração válida para forçar esse caminho; validar naturalmente se ocorrer nova falha.
- **Referências de integração**: [compatibilidade Gemini/OpenAI](https://ai.google.dev/gemini-api/docs/openai), [troubleshooting oficial](https://ai.google.dev/gemini-api/docs/troubleshooting).

### [x] Microsprint 14.1 — Histórico local de análises
- **Objetivo**: permitir que a pessoa consulte análises anteriores no protótipo sem criar conta, banco ou endpoint de persistência.
- **Escopo**: salvar somente por ação explícita do usuário, usando `localStorage`; limitar a 10 registros; mostrar domínio, data, score, risco e trechos curtos das evidências; permitir remover um registro ou apagar todos; apresentar aviso de que os dados ficam somente no navegador.
- **Privacidade e segurança**: não salvar URL completa, caminho, query string, fragmento, HTML da página, credenciais nem prompt. Inserir conteúdo armazenado como texto inerte. Tratar indisponibilidade/quota do armazenamento sem quebrar a análise.
- **Fora do escopo**: login, sincronização entre dispositivos, persistência no backend/banco, download/exportação e mudança do contrato da API.
- **Critérios de aceite**: análise só entra no histórico após clicar em “SALVAR NO HISTÓRICO”; lista persiste ao recarregar no mesmo navegador; remoção individual e limpeza total atualizam lista e contador; no máximo 10 itens; nenhuma URL completa ou HTML é armazenado; indisponibilidade de `localStorage` mostra mensagem compreensível e não interrompe o fluxo de análise.
- **Validação**: em 2026-09-28, o usuário confirmou que salvar e remover relatórios funcionaram no navegador. A validação foi manual; nenhum teste automatizado foi executado nesta sessão.

### [x] Microsprint 14.2 — Exportar relatório em Markdown
- **Objetivo**: permitir que o usuário baixe um relatório legível e portátil, sem depender de conta ou serviço externo.
- **Escopo**: incluir ação de download no resultado atual e em cada item do histórico. Gerar arquivo `.md` local com domínio, data, score heurístico, nível de risco e até 10 evidências já armazenadas; nomear arquivo com domínio e data.
- **Privacidade e segurança**: não incluir URL completa, query, fragmento, HTML, prompt ou segredo. Escapar caracteres Markdown e normalizar quebras de linha em texto de evidência para impedir que conteúdo da página injete estrutura no relatório. Usar Blob/Object URL no navegador e revogar o URL temporário.
- **Fora do escopo**: PDF, envio do arquivo para servidor, alteração da API, acesso à página novamente e persistência remota.
- **Critérios de aceite**: o resultado atual pode ser baixado sem antes ser salvo no histórico; relatórios salvos também podem ser baixados; o Markdown contém score/risco/achados e ressalva de score heurístico; o nome é seguro; nenhum endereço completo, HTML ou chave é incluído.
- **Validação**: em 2026-09-28, o usuário confirmou que o download funcionou. A verificação manual do conteúdo do arquivo não foi relatada separadamente; nenhum teste automatizado foi executado nesta sessão.

### [x] Microsprint 14.3 — Transparência sobre envio de texto ao modelo
- **Motivo**: a interface informa que a análise semântica é opcional, mas ainda não explica que, quando habilitada, um recorte de texto e sinais de controles da página são enviados ao provedor de IA.
- **Escopo**: mostrar antes do botão de análise um aviso claro de que o RASTRO acessa a URL no scanner e, quando a etapa semântica estiver ativa, envia recorte limitado de texto/sinais de controles ao provedor configurado (atualmente Gemini); explicitar que HTML integral não é enviado e que as regras determinísticas continuam disponíveis. Separar o aviso estático do estado dinâmico de cada análise.
- **Fora do escopo**: mudar a configuração global do LLM, introduzir consentimento por análise ou alterar o request/contrato da API.
- **Critérios de aceite**: o aviso aparece antes da ação e continua visível durante/depois da análise; status híbrido, fallback e erros continuam em uma área dinâmica separada; conteúdo corresponde ao payload montado no backend; nenhuma mudança no fluxo `POST /api/scan`.
- **Validação**: após a atualização, o usuário respondeu “ok, prossiga”; não relatou problema visual. Nenhum teste automatizado foi executado nesta sessão.

### [x] Microsprint 14.4 — Explicar o score no resultado e no relatório Markdown
- **Motivo**: a interface mostra valores como “5%”, embora o score seja uma soma heurística de pontos por severidade e não uma probabilidade calibrada. O usuário deve conseguir entender de onde vem a escala e como interpretar as faixas.
- **Escopo**: acrescentar ao resultado uma seção expansível com pesos por severidade, limite do score e faixas de risco; incluir a mesma explicação no relatório Markdown atual e histórico. Manter o indicador e algoritmo atuais.
- **Fora do escopo**: alterar score, severidades, faixas, API, regras, layout geral, histórico ou dados armazenados.
- **Critérios para concluir**: UI e exportação explicam pesos baixa=5, média=10, alta=20, crítica=30; score limitado a 100; faixas 0–24 baixo, 25–49 moderado, 50–74 elevado e 75–100 crítico; esclarecem que o símbolo “%” não é probabilidade de manipulação e que os sinais exigem contexto. O detalhe é acessível e fechado por padrão. Nenhum caminho de análise ou formato de API muda.
- **Validação**: o usuário autorizou seguir após a entrega; não relatou falhas. Nenhum teste automatizado foi executado nesta sessão.

### [x] Microsprint 14.5 — Mostrar gravidade e origem dos achados
- **Motivo**: o contrato da API já retorna a severidade e o motor de cada achado, mas a tela, o histórico e o Markdown não mostram essa informação. A pessoa não consegue distinguir um sinal produzido por regra determinística de uma interpretação semântica da IA.
- **Escopo**: exibir gravidade e origem em cada achado do resultado; guardar esses dois campos no histórico local; incluir ambos nos itens históricos e na exportação Markdown. Compatibilidade com relatórios antigos deve ser preservada, indicando origem/gravidade não informada quando esses campos não existirem.
- **Fora do escopo**: alterar critérios do detector, severidade, score, API, conteúdo enviado ao LLM, estrutura visual geral ou exigir nova análise para ler itens antigos.
- **Critérios para concluir**: cada achado novo mostra severidade e origem traduzidas; relatórios novos persistem os dois campos; histórico e downloads mostram as informações; entradas antigas continuam abrindo e indicam os metadados ausentes sem falha. Nenhum conteúdo do site é interpretado como HTML executável.
- **Validação**: o usuário autorizou seguir após a entrega; não relatou falhas. Nenhum teste automatizado foi executado nesta sessão.

### [x] Microsprint 14.6 — Contextualizar evidências e orientar revisão
- **Motivo**: gravidade e origem tornam os achados mais transparentes, mas quem usa ainda precisa deduzir por que o sinal apareceu e o que conferir na página. Sem contexto, um sinal heurístico pode ser interpretado como conclusão definitiva.
- **Escopo**: acrescentar uma explicação recolhível por achado para as categorias conhecidas, mostrando o motivo técnico do sinal e uma verificação contextual recomendada. Incluir a explicação completa no Markdown. Persistir somente o ID da categoria necessário para recuperar a explicação; compatibilidade com relatórios antigos por mensagem genérica.
- **Fora do escopo**: criar novas regras ou findings, alterar severidade/score/API, fazer checagem de fatos externos, fornecer orientação jurídica ou afirmar intenção manipulativa.
- **Critérios para concluir**: regras determinísticas e categorias semânticas atuais têm explicação apropriada; texto diferencia evidência observada de contexto ainda não verificado; achados desconhecidos e relatórios antigos mostram orientação genérica; conteúdo do site continua renderizado como texto inerte. A análise, o score e o contrato da API não mudam.
- **Validação**: em 2026-09-28, o usuário confirmou que a explicação e a exportação Markdown funcionaram. Nenhum teste automatizado foi executado nesta sessão.

### [x] Microsprint 14.7 — Preservar metadados da execução no histórico e relatório
- **Motivo**: a tela mostra se a etapa semântica funcionou, foi ignorada ou usou fallback, mas os relatórios históricos e downloads atuais perdem esse contexto. Sem os metadados, não é possível comparar uma execução híbrida com uma determinística depois.
- **Escopo**: guardar e exportar somente os metadados já retornados por `meta`: método (`deterministic`/`hybrid`), status semântico, categoria segura de indisponibilidade, duração, quantidade de elementos analisados e regras aplicadas. Exibir um resumo no histórico e uma seção no Markdown. Manter os dados locais e não salvar URL completa, conteúdo da página, resposta bruta ou segredo.
- **Fora do escopo**: alterar o backend, modelo, análise, contrato, lógica de score ou publicar os metadados externamente.
- **Critérios para concluir**: relatórios novos exibem status e estatísticas corretos; falhas mostram somente a categoria segura já presente na API; registros antigos seguem funcionando e indicam metadados não registrados; nenhuma informação da página ou segredo é acrescentado ao armazenamento.
- **Validação**: em 2026-09-28, o usuário confirmou que ambos funcionaram e autorizou seguir. A validação foi manual; nenhum teste automatizado foi executado nesta microsprint. Não houve falha natural do provedor nesta validação.

### [x] Microsprint 14.8 — Atualizar runbook Docker-first e reconciliar documentação
- **Motivo**: o Docker Compose é o fluxo local validado pelo usuário, mas o README e o handoff ainda priorizam o servidor Python direto e descrevem como pendente a integração Gemini no Docker. As limitações da API também podem ser confundidas com os recursos locais da interface.
- **Escopo**: documentar pré-requisito Docker Desktop, build/inicialização, health check, endereços da aplicação e Swagger, logs, restart, rebuild e parada; manter Python como alternativa e registrar que ele não usa o isolamento de egress do Compose. Atualizar o status real do Gemini e esclarecer que histórico/download são locais no navegador, não recursos persistidos pela API.
- **Fora do escopo**: mudar código da aplicação, configuração/segurança dos containers, integração LLM, executar comandos Docker na máquina do usuário ou criar persistência remota.
- **Critérios para concluir**: comandos e rotas coincidem com `compose.yaml` e `backend/main.py`; a documentação explica que o Docker Desktop precisa estar rodando e que `health: starting` é transitório; diferencia explicitamente recursos do frontend e da API; não afirma que existe deploy público.
- **Validação**: revisão estática da documentação e `git diff --check` passaram; em 2026-09-28, o usuário confirmou que a atualização está correta. Nenhum teste de aplicação foi executado nesta microsprint.

### [x] Microsprint 14.9 — Rastrear a evidência até o DOM capturado
- **Motivo**: o relatório apresenta o trecho que gerou um achado, mas não indica em qual elemento do DOM capturado ele foi encontrado. Isso dificulta a conferência manual da evidência.
- **Escopo**: localizar no HTML capturado o trecho entre aspas da evidência e expor um campo opcional `findings[].dom_reference`, contendo somente tags e posições de irmãos (`tag:nth-of-type(n)`). Exibir a referência de forma recolhível nos achados, no histórico local e no Markdown, acompanhada de uma nota sobre seus limites.
- **Privacidade e segurança**: o caminho não inclui texto, IDs, classes ou outros atributos da página; renderizá-lo como texto inerte. Não enviar HTML adicional ao LLM nem persistir conteúdo integral da página.
- **Fora do escopo**: mudar as regras de detecção, score, severidade, análise LLM, captura/renderização do navegador, armazenamento remoto ou implementar um seletor permanente para acompanhar mudanças no site.
- **Critérios para concluir**: quando um trecho curto citado for localizado, a API retorna um caminho posicional limitado; quando a evidência não tiver citação localizável, o campo é `null`; a interface não mostra referências fora do formato permitido e explica que a estrutura pode mudar e que o caminho não prova visibilidade; histórico antigo continua legível.
- **Validação**: revisão estática e `git diff --check` concluídos sem erros de whitespace. Em 2026-09-28, o usuário confirmou que estava correto e autorizou prosseguir. Nenhum teste automatizado foi executado nesta microsprint.

### [x] Microsprint 14.10 — Identificar o domínio final nos relatórios
- **Motivo**: quando uma página redireciona, o resultado atual identifica o domínio final analisado, mas o histórico e o Markdown podem registrar o hostname que a pessoa digitou. Isso deixa o relatório inconsistente com a análise.
- **Escopo**: montar o snapshot de relatório usando `apiData.domain`, que representa o domínio final carregado pelo backend, com fallback para o hostname digitado caso o campo não venha na resposta. Documentar a diferença entre `url` solicitada e `domain` analisado.
- **Privacidade**: continuar armazenando/exportando apenas o domínio, nunca a URL completa, caminho, query ou fragmento.
- **Fora do escopo**: mudar redirects, política anti-SSRF, forma de validação de URL, exibir/salvar a URL original, alterar o score ou o esquema de histórico.
- **Critérios para concluir**: para navegação sem redirect, histórico/Markdown preservam o domínio já exibido; após redirect, identificam o domínio final reportado pela API; relatórios antigos continuam válidos; fallback cobre respostas antigas sem `domain`.
- **Validação**: em 2026-09-28, após reconstruir e analisar um endereço com redirect, o usuário confirmou que `example.com` apareceu como domínio analisado. A confirmação separada no histórico e no arquivo Markdown não foi relatada; ambos usam o mesmo domínio do snapshot. Nenhum teste automatizado foi executado.

### [x] Microsprint 14.11 — Explicar redirecionamentos entre domínios
- **Motivo**: após seguir uma URL redirecionada, mostrar apenas o domínio final pode surpreender quem submeteu outro domínio e deixar ambíguo qual endereço iniciou a análise.
- **Escopo**: quando os hostnames diferirem, mostrar no resultado a origem e o domínio final analisado; preservar os dois hostnames no histórico local e descrevê-los no Markdown. Tratar diferenças apenas de maiúsculas ou prefixo `www.` como mesmo domínio para não sinalizar uma troca cosmética.
- **Privacidade**: guardar e exportar somente hostnames; nunca a URL completa, caminho, query string, fragmento ou HTML. Inserir valores como texto inerte.
- **Fora do escopo**: alterar o seguimento de redirects, a política anti-SSRF, o contrato da API, o score ou a análise semântica.
- **Critérios para concluir**: redirect para outro domínio é explicado na tela, no histórico e no Markdown; sem mudança real de domínio, a nota não aparece; relatórios antigos continuam válidos e não exibem aviso; nenhuma URL completa passa a ser armazenada.
- **Validação**: em 2026-09-28, o usuário confirmou que o aviso de redirecionamento funcionou. A validação manual de histórico e Markdown não foi relatada; ambos usam os mesmos hostnames do resultado. Nenhum teste automatizado foi executado.

### [x] Microsprint 14.12 — Esperar a estabilização do DOM com limite
- **Motivo**: páginas com renderização client-side podem acrescentar texto depois de `DOMContentLoaded`; uma pausa fixa pode encerrar cedo em páginas lentas e esperar demais em páginas que já estabilizaram.
- **Escopo**: substituir a pausa fixa por consultas a cada 250 ms de uma assinatura compacta do texto/DOM. Aguardar no mínimo 2.000 ms, encerrar depois de 750 ms sem mudanças ou no teto configurável (padrão 3.500 ms; limite 0–5.000 ms). Revalidar a URL final se ocorrer navegação client-side durante a espera.
- **Privacidade e segurança**: manter apenas a assinatura em memória durante a captura, sem registrar texto no log; não usar `networkidle`; preservar o filtro de requests e revalidar o destino final antes de extrair os dados.
- **Fora do escopo**: aumentar limites do LLM, contornar bloqueios anti-bot/login, garantir que todo conteúdo dinâmico seja carregado ou alterar as regras de score.
- **Critérios para concluir**: a janela termina por estabilidade ou pelo teto; configuração `0` desativa a espera; páginas públicas continuam passando pelos mesmos controles SSRF; documentação e valores padrão refletem o comportamento adaptativo.
- **Validação**: em 2026-09-28, o usuário confirmou que conferiu a espera adaptativa. Os valores de duração e contagem de elementos não foram registrados; nenhum teste automatizado foi executado nesta microsprint.

### [x] Microsprint 14.13 — Exigir preços distintos para sinalizar ancoragem
- **Motivo**: uma análise anterior sinalizou ancoragem com evidência repetida do mesmo valor (`R$ 79,99 R$ 79,99`), sem demonstrar uma comparação entre preço de referência e preço atual.
- **Escopo**: só produzir o finding quando um elemento de preço antigo/riscado e um bloco próximo e compacto apresentarem valores monetários distintos na mesma moeda. Normalizar separadores e repetição de valores para não contar a mesma quantia duas vezes; manter no máximo um achado por página e citar o texto literal do bloco.
- **Privacidade e segurança**: usar apenas o HTML/texto já capturado, manter a evidência curta e inerte e não registrar nem persistir conteúdo adicional da página.
- **Fora do escopo**: inferir se o desconto é real, comparar preços com fontes externas, alterar pesos/score, introduzir LLM ou mudar o contrato da API.
- **Critérios para concluir**: valores repetidos/iguais não geram `price_anchoring`; duas quantias distintas no mesmo bloco associado a um seletor de preço antigo podem gerar um único sinal com evidência localizável; outras regras e relatórios permanecem compatíveis.
- **Validação**: em 2026-09-28, o usuário autorizou prosseguir após a implementação; não relatou separadamente os valores observados nos dois casos. Revisão estática e `git diff --check` passaram; nenhum teste automatizado foi executado.

### [x] Microsprint 14.14 — Exibir o volume de texto visível capturado
- **Motivo**: o estado “sem texto suficiente” não mostra quanto texto foi extraído. A contagem ajuda a diferenciar uma captura curta de uma página longa cujo texto não passou pelos critérios da etapa semântica.
- **Escopo**: retornar `meta.visible_text_characters` com o total de caracteres de `body.innerText` capturado; exibir a contagem no resultado e incluir no resumo do histórico local e na exportação Markdown. Preservar a leitura de relatórios antigos sem esse campo.
- **Privacidade**: armazenar/exportar somente a quantidade, nunca o texto capturado; explicar que a contagem total não é a quantidade enviada ao LLM, que continua limitada a 12.000 caracteres.
- **Fora do escopo**: mudar o limiar do LLM, conteúdo do prompt, captura do DOM, regras determinísticas, score ou persistência remota.
- **Critérios para concluir**: a API retorna um inteiro não negativo; o resultado mostra a contagem sem afirmar que todo texto foi enviado ao modelo; histórico e Markdown preservam somente o número; registros antigos continuam válidos.
- **Validação**: em 2026-09-28, o usuário mostrou `12.097` caracteres no resultado e no histórico, e confirmou que o relatório Markdown contém `12097` sem incluir o texto da página. Registros anteriores sem a métrica continuam legíveis. A análise OLX também mostrou o finding de preço esperado; o provedor atingiu o limite de uso e o fallback determinístico concluiu. Validação manual concluída; nenhum teste automatizado foi executado.

### [x] Microsprint 14.15 — Limitar o tamanho da URL submetida
- **Motivo**: o contrato não limitava o tamanho do endereço submetido, permitindo que entradas excessivamente longas chegassem ao fluxo de captura.
- **Escopo**: rejeitar no backend URLs acima de 2.048 caracteres após aparar espaços e verificar novamente depois de acrescentar `https://`; validar também na interface e apresentar erro compreensível. A interface deve traduzir erros `422` de validação da API sem tratá-los como falha de acesso. A rejeição deve acontecer antes de iniciar a verificação anti-SSRF ou o navegador.
- **Privacidade e segurança**: não registrar nem persistir a URL rejeitada; não enfraquecer as validações existentes de esquema, hostname e SSRF.
- **Fora do escopo**: impor limite ao corpo HTTP completo, alterar limites de captura/LLM, criar rate limit ou mudar a forma como URLs válidas são analisadas.
- **Critérios para concluir**: entrada acima do limite é rejeitada com HTTP 422 e mensagem de validação clara antes da captura; frontend exibe tanto a validação local como o erro 422 do backend junto ao campo; URL dentro do limite continua no fluxo atual; frontend e contrato documentam o mesmo valor; não há acesso à página para a entrada inválida.
- **Validação**: em 2026-09-29, o usuário confirmou que a URL acima do limite exibe “A URL deve ter no máximo 2.048 caracteres.” Não houve nova análise de URL pública normal nessa confirmação; o caminho de sucesso não foi alterado. Nenhum teste automatizado foi executado.

### [x] Microsprint 14.16 — Exigir evidência visível para timer de urgência
- **Motivo**: a regra atual classifica a presença de seletores/classes `countdown` ou `timer` no HTML como urgência alta, mesmo se o elemento estiver oculto ou vazio.
- **Escopo**: usar o Playwright para recolher, em pequena quantidade, texto de contadores explicitamente nomeados, visíveis na viewport e com formato de tempo reconhecível. Só esse sinal pode acionar a variante de severidade alta. Manter os padrões textuais de urgência já existentes como achados médios. Não considerar as palavras isoladas “timer” ou “countdown” evidência textual.
- **Privacidade e segurança**: extrair somente trechos curtos em memória, sem registrar, guardar ou enviar conteúdo adicional ao LLM; usar `textContent` renderizado como texto inerte nos relatórios existentes.
- **Fora do escopo**: validar se o prazo é real, investigar histórico de preços, mudar score/pesos, criar novas categorias ou ampliar o texto enviado ao LLM.
- **Critérios para concluir**: classe de contador ausente, oculta ou vazia não produz finding alto; contador visível com valor temporal produz um único finding de urgência alta com evidência literal curta; linguagem explícita de urgência continua detectável em severidade média; a página neutra e os outros findings não mudam.
- **Validação**: em 2026-10-16, `backend/test_rendered_evidence.py` passou no Python local e dentro do container `rastro-api-1` (imagem reconstruída no mesmo dia): timer visível com valor temporal gera urgência alta; timer oculto ou vazio não gera achado. A conferência em página real continua opcional para o usuário.

### [x] Microsprint 14.17 — Exigir contexto para pré-seleção de marketing
- **Motivo**: a regra atual pode pontuar qualquer checkbox marcado sem rótulo, embora isso não indique que a opção pré-selecionada seja publicidade, newsletter ou oferta.
- **Escopo**: o Playwright deve observar o estado atual do checkbox, rótulos associados e rótulos visíveis na viewport. Emitir achado apenas se o checkbox estiver marcado e o texto do rótulo mencionar marketing, newsletter, oferta ou categoria equivalente já coberta pela regra. Remover a heurística que classifica checkbox sem rótulo como suspeito.
- **Privacidade e segurança**: recolher somente trechos curtos em memória; não registrar, persistir nem enviar ao LLM evidência adicional.
- **Fora do escopo**: detectar todos os tipos de pré-seleção, inferir intenção em campos sem rótulo, mudar score/pesos ou introduzir nova categoria.
- **Critérios para concluir**: checkbox marcado ligado a rótulo visível de marketing pode gerar finding; checkbox comum, checkbox sem rótulo ou com rótulo oculto não gera finding de pré-seleção; campo desmarcado não gera finding; demais regras continuam no fluxo atual.
- **Validação**: em 2026-10-16, `backend/test_rendered_evidence.py` passou no Python local e dentro do container `rastro-api-1`: checkbox de marketing pré-marcado com rótulo visível gera achado; checkbox comum marcado, checkbox de marketing desmarcado e checkbox sem rótulo visível não geram achado. A conferência em página real continua opcional para o usuário.

### [x] Microsprint 14.18 — Separar escassez de urgência vaga
- **Motivo**: a regra de falsa escassez também sinalizava palavras vagas como “corra” e “acabando” sem referência a estoque, unidades ou disponibilidade, e as rotulava como escassez alta.
- **Escopo**: exigir quantidade explícita ou contexto de estoque, unidades, itens, vagas ou oferta limitada para `fake_scarcity`. Tratar chamadas explícitas para agir logo (“corra”, “hurry”, “apresse-se”, “act now”) como evidência textual de urgência média. Palavras ambíguas isoladas, como “acabando”, não devem gerar finding.
- **Privacidade e segurança**: usar texto/HTML já capturados; não ampliar coleta, payload enviado ao LLM, armazenamento ou evidência persistida.
- **Fora do escopo**: verificar se estoque ou prazo são reais, alterar pesos do score, criar categorias novas ou mudar a extração do DOM.
- **Critérios para concluir**: chamadas vagas deixam de aparecer como falsa escassez; quantidade/indicação explícita de disponibilidade limitada continua detectável como escassez; frases de pressão para agir passam para urgência; demais regras mantêm o fluxo.
- **Validação**: em 2026-10-16, o usuário executou os quatro casos no Python local: “Acabando” não gera finding; “Corra para aproveitar!” gera urgência; “Estoque acabando” e “Restam 2 unidades” geram escassez. No mesmo dia, a imagem foi reconstruída e `backend/test_rendered_evidence.py` repetiu os quatro casos dentro do container `rastro-api-1`, com os mesmos resultados.

### [x] Microsprint 14.19 — Ignorar texto de escassez não renderizado
- **Motivo**: a regra de escassez ainda examinava o HTML estático, podendo encontrar termos em elementos ocultos por CSS, `hidden` ou `aria-hidden`.
- **Escopo**: coletar no Playwright textos curtos dos mesmos tipos de elementos candidatos somente quando o elemento e seus ancestrais não estiverem ocultos e o elemento tiver geometria renderizada. Considerar também conteúdo renderizado abaixo da dobra. A regra deve usar essa lista no caminho da API; a lista adicional não deve ser enviada ao LLM nem armazenada.
- **Privacidade e segurança**: limitar a coleta aos primeiros 500 elementos candidatos e a 200 caracteres por trecho; manter a evidência final curta; reusar a captura já feita e não registrar nem persistir os textos intermediários.
- **Fora do escopo**: mudar a regra lexical definida na 14.18, exigir que o conteúdo esteja na viewport inicial, validar a veracidade da escassez ou mudar o score.
- **Critérios para concluir**: elemento renderizado com “restam 2 unidades” pode gerar finding mesmo abaixo da dobra; o mesmo texto sob `display:none`, `visibility:hidden`, opacidade quase zero, `hidden` ou ancestral `aria-hidden=true` não gera finding; demais regras permanecem inalteradas.
- **Validação**: em 2026-10-16, `backend/test_rendered_evidence.py` passou no Python local e dentro do container `rastro-api-1` após rebuild: “restam 2 unidades” renderizado abaixo da dobra gera achado; o mesmo texto sob `display:none`, `visibility:hidden`, `hidden`, `aria-hidden` em ancestral ou opacidade quase zero não gera achado; na mesma página, a evidência cita somente o trecho visível. A conferência em página real continua opcional para o usuário.

### [x] Microsprint 14.20 — Ignorar texto de confirmshaming não renderizado
- **Motivo**: a regra de confirmshaming ainda varria o HTML estático com BeautifulSoup, podendo sinalizar frases de recusa presentes em elementos ocultos por CSS, `hidden` ou `aria-hidden` — a mesma classe de falso positivo corrigida na 14.19 para escassez.
- **Escopo**: reutilizar a coleta de candidatos renderizados do Playwright, incluindo `a` entre os elementos elegíveis, e alimentar também a regra de confirmshaming com essa lista. Renomear a coleta e o campo interno para `collect_rendered_text_candidates`/`rendered_text_evidence`, já que a lista passa a servir às duas regras textuais. Manter o fallback estático da regra para chamadas fora do fluxo com navegador. Conteúdo abaixo da dobra continua elegível.
- **Privacidade e segurança**: os limites já existentes se mantêm (500 candidatos, 200 caracteres por trecho); a evidência continua curta e inerte, em memória apenas, sem envio ao LLM nem persistência.
- **Fora do escopo**: mudar o léxico de confirmshaming, validar intenção da recusa, estender a coleta renderizada a outras regras (overlay, preço) ou alterar o score.
- **Critérios para concluir**: link de recusa renderizado, inclusive abaixo da dobra, gera achado; o mesmo texto sob `display:none`, `visibility:hidden`, `hidden` ou ancestral `aria-hidden` não gera; na mesma página, a evidência cita somente o trecho visível; demais regras mantêm o fluxo.
- **Validação**: em 2026-10-16, `backend/test_rendered_evidence.py` passou no Python local e dentro do container `rastro-api-1` reconstruído: “Não, obrigado” renderizado abaixo da dobra gera achado; as quatro variantes ocultas não geram; a evidência ignora o trecho oculto na mesma página. `test_overlay_detection.py` (6 casos) e `test_scraper_routing.py` (6 casos) seguem passando. A conferência em página real continua opcional para o usuário.

### [x] Microsprint 14.21 — Ignorar preço de referência não renderizado
- **Motivo**: a regra de ancoragem ainda localizava `del`/`s`/`price-old` no HTML estático; um preço de referência oculto podia sustentar o achado — última regra ainda baseada em markup estático.
- **Escopo**: coletar no Playwright os elementos de preço antigo efetivamente renderizados (mesma verificação de ocultação das demais coletas, sem exigir posição na viewport) junto com os blocos ancestrais compactos (até 4 níveis, 180 caracteres) que a regra já usava. A regra consome `rendered_price_evidence` e mantém o mesmo critério de valores distintos da 14.13, com fallback estático fora do fluxo de navegador.
- **Privacidade e segurança**: limites de 100 elementos candidatos, 10 blocos e 200 caracteres por trecho; nada é enviado ao LLM, registrado em log nem persistido.
- **Fora do escopo**: mudar o critério de comparação de preços, validar desconto real, cobrir outros formatos de moeda ou alterar score/severidade.
- **Critérios para concluir**: `del`/`price-old` renderizado com preço distinto no mesmo bloco, inclusive abaixo da dobra, gera achado; elemento oculto por estilo/`hidden`/`aria-hidden` não gera; `del` oculto com preço atual visível não gera; valores repetidos continuam sem achado (regressão 14.13).
- **Validação**: em 2026-10-16, `backend/test_rendered_evidence.py` passou no Python local e dentro do container `rastro-api-1` reconstruído: bloco `del`+preço atual abaixo da dobra gera achado; quatro variantes ocultas não geram; `R$ 79,99` repetido não gera. Regressões de overlay e routing seguem passando. A conferência em página real continua opcional para o usuário.

### [x] Microsprint 14.22 — Ignorar texto estacionado fora da tela
- **Motivo**: elementos renderizados posicionados inteiramente em espaço negativo (ex.: `position:absolute; left:-9999px`) mantêm geometria e `innerText`, então ainda alimentavam as regras de escassez, confirmshaming e ancoragem — embora o usuário nunca os veja.
- **Escopo**: nas coletas de candidatos de texto e de contexto de preço, descartar elementos cujo retângulo termina fora da área visível em coordenadas negativas (`rect.right <= 0` ou `rect.bottom <= 0`). Conteúdo abaixo da dobra mantém limites positivos e continua elegível, conforme definido na 14.19. Elementos parcialmente fora da tela seguem elegíveis.
- **Privacidade e segurança**: nenhum dado novo é coletado; os limites existentes se mantêm e nada é enviado ao LLM, registrado ou persistido.
- **Fora do escopo**: outras formas de ocultação visual (recorte por `clip-path`, `text-indent` negativo, camadas cobertas por outros elementos), mudança nas coletas que já exigem interseção com a viewport (timer, checkbox, overlay, consentimento) ou alteração de score.
- **Critérios para concluir**: texto à esquerda/acima da tela não gera achado de escassez, confirmshaming nem ancoragem; conteúdo abaixo da dobra e parcialmente fora da tela continuam elegíveis; demais regras mantêm o fluxo.
- **Validação**: em 2026-10-16, `backend/test_rendered_evidence.py` passou no Python local e dentro do container `rastro-api-1` reconstruído: quatro casos de texto estacionado fora da tela não geram achado e o elemento parcialmente visível continua elegível. As demais suítes locais seguem passando. A conferência em página real continua opcional para o usuário.

### [x] Microsprint 14.23 — Urgência textual só em texto renderizado
- **Motivo**: a variante textual de urgência ainda varria o `body.innerText` completo, que inclui texto posicionado fora da tela e oculto por CSS — o último caminho de regra a consumir texto bruto em vez de candidatos renderizados.
- **Escopo**: no fluxo com navegador, a regra de urgência textual passa a avaliar `rendered_text_candidates` (mesma lista das regras de escassez e confirmshaming) em vez do `innerText` integral. O achado de timer visível de severidade alta e o fallback ao texto completo fora do fluxo de navegador são preservados.
- **Privacidade e segurança**: reutiliza a lista já coletada em memória; nada novo é enviado ao LLM, registrado ou persistido.
- **Fora do escopo**: alterar o léxico de urgência, o sinal de timer, o score ou a coleta de candidatos.
- **Critérios para concluir**: frase de urgência em elemento oculto ou estacionado fora da tela não gera achado; frase renderizada continua gerando urgência média; timer visível segue gerando urgência alta.
- **Validação**: em 2026-10-16, `backend/test_rendered_evidence.py` passou no Python local e dentro do container `rastro-api-1` reconstruído: “Corra!” fora da tela e oculto não geram achado; “Corra para aproveitar!” renderizado gera urgência média; os casos de timer da 14.16 seguem passando. A conferência em página real continua opcional para o usuário.

### [x] Microsprint 14.24 — Reconciliar contrato com as regras renderizadas
- **Motivo**: `docs/api-contract.md` (v0.3) ainda descrevia só a coleta renderizada da escassez e omitia as mudanças das 14.20–14.23; o schema em `backend/main.py` também listava um valor `engine="stub"` inexistente.
- **Escopo**: revisar o contrato contra `main.py`/`analyzer.py`; atualizar a seção de regras para registrar que `confirmshaming`, a urgência textual e `price_anchoring` também consomem evidência renderizada e que trechos estacionados fora da tela são descartados; corrigir o comentário do schema para os motores realmente emitidos (`deterministic`, `llm`); bump do documento para v0.4.
- **Privacidade e segurança**: nenhuma mudança funcional; apenas documentação e comentário.
- **Fora do escopo**: alterar campos, respostas de erro ou comportamento das regras.
- **Critérios para concluir**: a seção de regras do contrato descreve as 7 regras como implementadas; o comentário de `Finding.engine` lista só valores emitidos; suítes seguem passando.
- **Validação**: em 2026-10-19, `backend/test_rendered_evidence.py` (24/24) e `backend/test_ssrf.py` (30/30) passaram no Python local; o contrato foi relido contra o código final. Não houve mudança funcional a validar no container.

---

## Fase 2 — Persistência anônima

### [x] Microsprint 15.1 — Histórico anônimo no servidor (modelo A)
- **Decisão de produto**: o usuário definiu o RASTRO como site de verificação pontual estilo VirusTotal — sem contas, sem login, sem fricção. O modelo B (contas) da proposta `docs/antigravity/PERSISTENCIA.md` foi descartado.
- **Escopo**: cookie opaco `rastro_hid` (HttpOnly, SameSite=Lax, 1 ano) emitido pela API; todo scan bem-sucedido grava automaticamente o resumo (domínio, score, risco, achados curtos, metadados) no SQLite local (`RASTRO_DB_PATH`, volume `api-data` no Compose); `GET /api/history`, `DELETE /api/history/{id}` e `DELETE /api/history` escopados à identidade; retenção de 100 itens; gravação best-effort não derruba o scan; frontend passa a listar o histórico do servidor e o botão “SALVAR NO HISTÓRICO” foi removido (auto-save).
- **Privacidade e segurança**: nenhum dado pessoal — o cookie é um identificador aleatório; URL completa, HTML e texto integral continuam fora do banco; evidências limitadas a 240 caracteres; anônimo não exige nenhuma ação.
- **Fora do escopo**: sincronização entre instalações/dispositivos, expiração por tempo, exportação do histórico inteiro, migração do `localStorage` antigo (fica órfão no navegador).
- **Critérios para concluir**: scan grava resumo acessível via `GET /api/history`; outra identidade não vê nem remove itens alheios (404); retenção mantém 100; scan sobrevive a falha de banco; contrato v0.5 documenta os endpoints.
- **Validação**: `backend/test_history.py` (18/18) passou no Python local e dentro do container `rastro-api-1` reconstruído; sintaxe do frontend conferida com `node --check`; regressões `test_rendered_evidence.py` e demais suítes seguem verdes. Em 2026-10-19, a persistência foi confirmada ponta a ponta no Compose: item inserido no volume `api-data` permaneceu acessível por `GET /api/history` após `docker compose restart api`, e `DELETE /api/history` o removeu (204). Observação: `docker compose exec` roda como root e, por `cap_drop: ALL`, não escreve em `/data` — probes devem usar `--user pwuser`. A conferência visual do histórico na interface fica para o usuário.

### [x] Microsprint 15.2 — Rate limit e cookie Secure (pré-requisitos de exposição)
- **Motivo**: a proposta `docs/antigravity/DEPLOY.md` identificou que abrir `/api/scan` publicamente sem controle de taxa permite abuso (cada scan abre um Chromium) e que o cookie precisa de `Secure` em HTTPS. Ambos são implementáveis e testáveis localmente, sem deploy.
- **Escopo**: janela deslizante em memória por IP de origem, `SCAN_RATE_LIMIT_PER_MINUTE` (padrão 10, 0 desativa), avaliada antes de qualquer I/O; exceder retorna `429` com `detail.code="RATE_LIMIT"` no formato de erro do scanner; cookie `rastro_hid` emite `Secure` quando `APP_ENV=production` (loopback segue confiável para o navegador, então o Docker local não quebra).
- **Privacidade e segurança**: o contador em memória guarda apenas timestamps por IP e expira em 60 s; nada é persistido.
- **Fora do escopo**: rate limit distribuído, banimento, limite por cookie, CAPTCHA, reverse proxy (fatia 15.3 do DEPLOY.md, que exige autorização).
- **Critérios para concluir**: a (limit+1)ª requisição do mesmo IP retorna 429 sem abrir navegador; outro IP não é afetado; cookie sem `Secure` em development e com `Secure` em production; contrato v0.6 documenta 429 e a flag.
- **Validação**: em 2026-10-19, `backend/test_history.py` (22/22) passou no Python local e dentro do container `rastro-api-1` reconstruído — incluindo 429 RATE_LIMIT, limite por IP e flags do cookie nos dois ambientes.

---

## Fases Futuras (Fora do primeiro checkpoint)
- **Deploy**: Depois do gate de segurança da Sprint 12, configurar deploy na Oracle Cloud (VPS). **Proposta de escopo em `docs/antigravity/DEPLOY.md` — aguarda autorização explícita do usuário; inclui rate limit e cookie `Secure` como pré-requisitos de exposição.**
- **Persistência remota**: banco para contas e sincronização de relatórios, em microsprint futura separada; histórico e exportação da 14.x são locais e não substituem esse trabalho. **Proposta de escopo em `docs/antigravity/PERSISTENCIA.md` — aguarda aprovação do usuário; proposta não autoriza implementação.**
