# RASTRO - Planejamento em Microsprints

O projeto será desenvolvido etapa por etapa (microsprints). O agente não pode avançar para a próxima sprint sem a aprovação do usuário na atual.

## Fase: Fundação e Protótipo (Sem Backend Funcional)

### Sprint 0 — Reconhecimento e plano, sem código
- **Escopo**: Fazer o agente entender o estado real do projeto lendo `STATE.md`, as regras e inspecionando os arquivos em `prototype/`.
- **Critério de Aceite**: O agente entrega um resumo do que entendeu e lista o plano, sem tocar em nenhuma linha de código da aplicação.

### Sprint 1 — Fundação e proteção do repositório
- **Escopo**: Organizar estrutura de pastas. Criar/atualizar `.gitignore` para barrar segredos. Criar `.env.example`.
- **Critério de Aceite**: Arquivos ignorados pelo Git corretamente. Nenhum segredo mockado. Ambiente base documentado.

### Sprint 2 — Inventário visual e direção aprovada
- **Escopo**: Inspecionar o HTML/CSS do `prototype/` (estética terminal/hacker). Apontar pequenos ajustes de UI, responsividade e acessibilidade.
- **Critério de Aceite**: O agente sugere uma lista de ajustes de frontend e **aguarda aprovação** antes de codificá-los.

### Sprint 3 — Polimento visual do protótipo
- **Escopo**: Aplicar os ajustes aprovados na Sprint 2. Preservar o design estático de "arte ASCII" do olho e os campos existentes.
- **Critério de Aceite**: Interface rodando localmente sem quebras visuais em desktop/mobile.

### Sprint 4 — Fluxo de interface com simulação explícita (Mocks)
- **Escopo**: Adicionar JS no front para simular os estados (URL inválida, analisando, falha, sucesso com dados falsos). Botão de enviar bloqueado durante análise.
- **Critério de Aceite**: A interface tem feedback interativo sem depender de backend real.

---

## Fase: Backend e Lógica

### Sprint 5 — Contrato da API, sem scraper
- **Escopo**: Definir o formato JSON para os requests/responses (como `POST /api/scan`). Tratar os cenários de erro e sucesso esperados.
- **Critério de Aceite**: Contrato documentado e validado. Frontend preparado para lidar com ele (ainda mockado).

### Sprint 6 — Backend mínimo (FastAPI)
- **Escopo**: Subir uma API FastAPI básica (Hello World e `GET /api/health`).
- **Critério de Aceite**: O endpoint responde localmente e a documentação do Swagger UI (FastAPI) está acessível.

### Sprint 7 — Barreira de URL e proteção contra SSRF
- **Escopo**: Impedir chamadas a IPs locais/privados (`127.0.0.1`, `10.x`, etc.) e verificar URLs maliciosas. 
- **Critério de Aceite**: Testes automatizados na API bloqueiam acessos à intranet e requisições HTTP inválidas.

### Sprint 8 — Worker Playwright isolado
- **Escopo**: Instalar Playwright no backend. Configurar para abrir uma página em contexto limpo (sem cookies de sessão), fazer scraping básico do DOM e fechar. Limite de 1 análise simultânea.
- **Critério de Aceite**: Consegue extrair o `<title>` e tags `<a>` de um site de teste com segurança e sem vazamento de memória.

### Sprint 9 — Regra Fase 1: Análise Determinística (Escassez/Urgência)
- **Escopo**: Implementar lógica via Regex/CSS para detectar gatilhos básicos ("Só restam X"). 
- **Critério de Aceite**: O backend recebe a URL, extrai o texto e retorna o array de `findings` se a regra determinística disparar, ou vazio caso contrário. Sem uso de LLM.

### Sprint 10 — Conectar a interface à API real
- **Escopo**: Trocar os mocks do frontend pelo `fetch` real batendo no backend rodando via Playwright.
- **Critério de Aceite**: O fluxo completo (inserir URL -> esperar -> ver resultado) funciona ponta a ponta na máquina local.

---

## Fases Futuras (Fora do primeiro checkpoint)
- **Fase 2 (LLM)**: Só entrará em cena após o MVP determinístico estar robusto. Será feita a integração com OpenRouter usando apenas prompts semânticos refinados, sem envio de credenciais no frontend.
- **Deploy**: Criação de Dockerfile e setup na Oracle Cloud (VPS).
- **Persistência**: Banco de dados para salvar relatórios históricos.
