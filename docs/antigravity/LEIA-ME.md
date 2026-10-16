# Projeto RASTRO - Pacote de Início

Bem-vindo ao pacote de inicialização do projeto RASTRO. Este diretório contém toda a documentação necessária para que um agente Antigravity (ou outro LLM) assuma o desenvolvimento do MVP de forma controlada, segura e em etapas (microsprints).

## Ordem de Leitura e Como Iniciar

Se você é o **usuário (Tech Lead)**:
1. Leia este `LEIA-ME.md` para entender a estrutura.
2. Revise o arquivo `CREDENCIAIS-E-SETUP.md` para preparar seu ambiente local (chaves, variáveis de ambiente, etc.).
3. Copie o conteúdo de `PROMPT-MESTRE-MVP.md` e cole no chat do Antigravity para iniciar a sessão de desenvolvimento com o Agente 3.

Se você é o **Agente 3 (Antigravity)**:
1. Comece lendo o `PROMPT-MESTRE-MVP.md` (fornecido pelo usuário no chat).
2. Siga as regras do arquivo raiz `GEMINI.md`.
3. Verifique o estado atual em `STATE.md`.
4. Leia o plano de ação em `MICROSPRINTS.md`.
5. Leia as `DECISOES-TECNICAS.md` para entender o stack e a arquitetura.

## Estrutura do Pacote

- `PROMPT-MESTRE-MVP.md`: O prompt inicial para dar contexto ao agente.
- `MICROSPRINTS.md`: O roteiro passo a passo do desenvolvimento. O agente fará uma sprint por vez.
- `DECISOES-TECNICAS.md`: Registro da arquitetura escolhida e alternativas.
- `CREDENCIAIS-E-SETUP.md`: O que o usuário precisa configurar, chaves locais (sem expor segredos no repo).
- `STATE.md`: O estado atual do repositório, problemas ativos e próximos passos.
- `HANDOFF.md`: Modelo de transição para quando a janela de contexto estiver cheia.
- `REFERENCIAS-E-LICENCAS.md`: Resumo dos projetos, artigos e protótipos fornecidos como referência.
- `../GEMINI.md` (na raiz do projeto): Regras do projeto que o Antigravity carrega automaticamente.

## Recomendações de Skills para o Antigravity

Recomendamos instalar as seguintes skills no workspace (via `npx skills add ...`) para aprimorar a capacidade do agente em áreas específicas:
- `fastapi` (stack do backend)
- `frontend-design` (design e UI)
- `ux-dark-patterns-audit` e `ux-heuristics-audit` (referência em UX, mas note que o RASTRO usará seu próprio motor de detecção)
- `pm-product-spec` (gestão de produto)

*(As skills não modificam sozinhas o projeto; elas apenas ensinam o agente sobre melhores práticas dessas áreas).*
