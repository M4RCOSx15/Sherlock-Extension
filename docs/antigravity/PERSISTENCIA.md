# Persistência remota — proposta de escopo (Fase 2)

> **Status:** PROPOSTA — aguarda aprovação do usuário antes de qualquer implementação.
> **Data:** 2026-10-19
> **Tipo:** microsprint de escopo, conforme exigido pelo backlog ("persistência exige escopo e validações próprias").

## 1. Problema

- **Fato atual:** resultados de análise só existem no navegador — até 10 resumos em `localStorage` e downloads Markdown gerados no cliente. A API não persiste nada; não há conta, identidade nem sessão de usuário.
- **Consequência:** o histórico desaparece ao trocar de navegador, dispositivo ou ao limpar o storage; não há como recuperar análises antigas nem usar o produto em dois lugares. Sem contas, o produto também não pode oferecer uso multiusuário nem cobrança futura.
- **Objetivo:** permitir que o usuário guarde e recupere suas análises entre dispositivos, preservando a minimização de dados que o produto pratica hoje.

## 2. Premissa não validada (risco principal)

Este documento assume que vale ter **contas de usuário** — mas a necessidade ainda não foi confirmada. Existe uma opção menor (ver §6, Alternativa A): histórico remoto anônimo, sem login. Confirmar qual das duas atende ao produto desejado antes de implementar.

## 3. Escopo proposto

**Dentro:**
- Cadastro/login simples (e-mail + senha) e sessão autenticada no mesmo serviço FastAPI.
- Persistência de **resumos de análise** por usuário: domínio final, data, score, risco, findings com evidência, metadados de execução — o mesmo recorte que o Markdown exporta hoje.
- Listagem e remoção de itens do histórico na interface, alimentada pelo servidor quando autenticado.
- Banco embutido (SQLite) no mesmo container da API, com volume Docker; sem novo serviço.

**Fora (explícito):**
- Persistir texto/HTML integral da página, URL completa ou payload do LLM — mantém a política de minimização.
- OAuth/social login, verificação de e-mail, recuperação de senha por e-mail, times/organizações, compartilhamento de relatórios, billing.
- Sincronização do `localStorage` antigo para o servidor (migração manual via reanálise).
- Deploy público, HTTPS, rate limiting — fase separada, depende desta.
- Qualquer envio adicional ao LLM ou coleta de dados de página além do atual.

## 4. Histórias de usuário

- Como usuário recorrente, quero que minhas análises fiquem salvas na minha conta para consultá-las de qualquer navegador.
- Como usuário, quero poder apagar um item do histórico remoto para não manter o que não preciso.
- Como usuário anônimo, quero continuar usando o scanner sem login para testar antes de criar conta (fluxo atual preservado).

## 5. Requisitos (testáveis)

1. `POST /api/auth/register` cria conta com e-mail único e senha com hash (scrypt/argon2, nunca texto plano); respostas de erro não revelam se o e-mail já existe.
2. `POST /api/auth/login` emite cookie de sessão `HttpOnly`+`SameSite=Lax`; `POST /api/auth/logout` a revoga.
3. `GET /api/history` retorna somente os resumos do usuário autenticado, ordenados por data, sem URL completa nem texto de página.
4. `DELETE /api/history/{id}` remove somente item do próprio usuário; item de outro usuário retorna `404`.
5. `/api/scan` continua funcionando sem autenticação e não grava nada quando anônimo; quando autenticado, grava o resumo da análise automaticamente.
6. Limite de retenção: manter no máximo 100 resumos por usuário, descartando os mais antigos.
7. Toda alteração de rota/payload/erro atualiza `docs/api-contract.md` e testes na mesma entrega.

## 6. Alternativas em aberto (decisão necessária)

| | A — Histórico anônimo | B — Contas (recomendada) |
|---|---|---|
| Modelo | Cookie de identidade gerado pelo servidor, sem login | E-mail + senha + sessão |
| Privacidade | Máxima — nada identifica a pessoa | Identidade explícita, mais dados |
| Habilita SaaS | Não | Sim (multiusuário, billing futuro) |
| Esforço | Menor | Maior |

## 7. Dependências, restrições e suposições

- **Dependências internas:** definição do modelo de conta (A/B), schema de sessão, migração do frontend para histórico remoto quando logado.
- **Dependências externas:** nenhuma — sem provedor novo; o egress do LLM não muda.
- **Restrições:** monolito FastAPI + SQLite (sem ORM pesado, estilo do projeto); containers read-only exigem volume montado para o arquivo do banco; contrato deve manter compatibilidade para clientes anônimos.
- **Suposições (a testar):** usuários aceitam criar conta para manter histórico (não validada — risco §2); retenção de 100 itens é suficiente; evidência textual dos findings pode persistir sem reclassificar o dado como sensível.

## 8. Métricas de sucesso

- Usuário autenticado vê o mesmo histórico em dois navegadores distintos.
- `GET /api/history` sem sessão retorna `401`; com sessão, ≤ 200 ms em volume local.
- Análise anônima continua produzindo resposta idêntica à atual (regressão de contrato).

## 9. Validação proposta

- Testes de API para cada requisito do §5 (registro, login, isolamento por usuário, retenção, fluxo anônimo intacto).
- `test_ssrf.py`, `test_rendered_evidence.py` e regressões seguem passando.
- Documento de privacidade atualizado: o que passa a existir no servidor, retenção e exclusão.
