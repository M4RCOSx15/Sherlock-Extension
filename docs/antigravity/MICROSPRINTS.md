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

---

## Fases Futuras (Fora do primeiro checkpoint)
- **Deploy**: Depois do gate de segurança da Sprint 12, configurar deploy na Oracle Cloud (VPS).
- **Persistência**: Banco de dados para salvar relatórios históricos.
