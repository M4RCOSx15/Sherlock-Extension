---
description: "Regras Fundamentais do Projeto RASTRO para agentes de IA"
trigger: "always_on"
---

# Regras do Projeto RASTRO

Este projeto é o SaaS RASTRO, uma ferramenta de auditoria de dark patterns e copywriting em páginas web.

## Regras de Comportamento do Agente (Antigravity e outros)
1. **Microsprints:** Trabalhe em UMA (1) única microsprint por vez (veja `docs/antigravity/MICROSPRINTS.md`).
2. **Aprovação Explícita:** Nunca comece a próxima sprint antes do usuário expressamente aprovar a conclusão da anterior.
3. **Escopo Mínimo:** Não crie arquivos redundantes, nem instale pacotes que não foram aprovados na sprint atual. Se a sprint atual focar no frontend estático, não instale o backend.
4. **Handoff e Estado:** Sempre, ao concluir uma sprint, atualize `docs/antigravity/STATE.md` com o que acabou de ser feito e eventuais problemas. Se solicitado, ou se o limite de contexto estiver próximo (cerca de 70%), pare de codificar, preencha o `docs/antigravity/HANDOFF.md` e espere a transição de sessão.
5. **Segurança:** Nunca, sob nenhuma circunstância, exiba ou comite dados sensíveis (API keys, senhas) ou salve HTML de terceiros sem filtragem severa. O `Playwright` no backend deve ser ativado com extrema blindagem contra chamadas SSRF.

Se tiver qualquer dúvida, pare e peça instruções. A regra é "Falhar de forma segura" e esperar intervenção humana.
