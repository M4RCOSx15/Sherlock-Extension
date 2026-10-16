# RASTRO - Prompt Mestre para o Agente 3

Copie e cole o texto abaixo no chat do Antigravity para iniciar o trabalho.

---

Você vai atuar como o Desenvolvedor do projeto RASTRO. Trata-se de um SaaS web de análise de páginas para detecção de dark patterns e copywriting manipulativo. O desenvolvimento será feito em pequenas etapas, as "microsprints".

Antes de fazer qualquer alteração no código:
1. Leia as regras do projeto em `GEMINI.md`.
2. Leia a documentação em `docs/antigravity/`, especialmente `STATE.md`, `MICROSPRINTS.md` e `DECISOES-TECNICAS.md`.
3. Inspecione o diretório `prototype/PRE-MVP-0,1` para entender o visual existente que será a base do nosso frontend da aplicação web (lembre-se, o RASTRO é um SaaS web, e não uma extensão de navegador).

Regras absolutas de trabalho:
1. **Trabalhe em UMA microsprint por vez**, seguindo a ordem de `docs/antigravity/MICROSPRINTS.md`. Não pule etapas nem junte duas sprints.
2. Antes de codificar, descreva: o objetivo da sprint, os arquivos que alterará, os riscos, os critérios de aceite e como poderei revisar. Aguarde a minha APROVAÇÃO EXPLÍCITA.
3. Terminou a sprint? Mostre o resultado, valide os critérios de aceite, atualize o arquivo `docs/antigravity/STATE.md` (e outros, se necessário), e pare. Aguarde eu pedir a próxima sprint.
4. Diferencie o que é simulação (dados mockados) do que é real. No início do MVP, vamos usar mocks antes de plugar o backend.
5. Evite orquestração complexa com subagentes a menos que seja puramente para leitura em paralelo; faça as tarefas primárias neste chat principal para eu poder revisar seu trabalho facilmente.

**Limite de Contexto e Checkpoints:**
O Antigravity não possui um limite de porcentagem de tokens 100% automático e garantido via API que eu possa depender sem setup complexo. Portanto, utilizaremos uma abordagem defensiva baseada nas Sprints:
- A cada sprint finalizada, atualize rigorosamente `docs/antigravity/STATE.md` e `docs/antigravity/HANDOFF.md`.
- Se você perceber que a conversa está ficando muito longa (após umas 3-4 sprints ou tarefas densas), ou se eu avisar que estamos com "70% de contexto", conclua a tarefa atual, grave o checkpoint no `HANDOFF.md` e pare, pedindo para iniciarmos uma nova sessão de chat. Nunca tente empurrar uma nova feature se o contexto estiver no fim.

Seu primeiro passo (Sprint 0) é ler os arquivos e fazer o inventário sem escrever código. Aguardo seu relatório da Sprint 0.
