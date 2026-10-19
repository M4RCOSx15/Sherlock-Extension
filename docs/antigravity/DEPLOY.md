# Deploy público — proposta de escopo (Fase 2)

> **Status:** PROPOSTA — aguarda autorização explícita do usuário. Deploy é ação irreversível de exposição pública; esta proposta não a autoriza.
> **Data:** 2026-10-19
> **Enquadramento:** site de verificação pontual estilo VirusTotal — simples, sem contas, scan → resultado.

## 1. Problema

- **Fato atual:** o RASTRO roda só em `127.0.0.1:8000` no Windows local, com proxy de egress e isolamento validados em Docker.
- **Consequência:** ninguém além do usuário consegue usar; o produto não existe publicamente.
- **Objetivo:** expor o scanner em um domínio público com HTTPS, mantendo as proteções atuais (egress, SSRF, read-only, sem privilégios) e adicionando o mínimo de blindagem que exposição pública exige.

## 2. O que muda ao abrir para a internet (decisões com risco)

1. **Abuso do scanner.** `/api/scan` abre um Chromium por requisição — sem controle de taxa, qualquer um pode usar o servidor como proxy de scraping ou derrubá-lo por custo. **Exige rate limit antes de publicar.**
2. **O cookie `rastro_hid` precisa de `Secure`.** Hoje é emitido sem a flag (localhost é HTTP); em produção HTTPS deve ser `Secure` — parametrizar por `APP_ENV`.
3. **CORS `*`.** Aceitável para API pública de consulta, mas com cookie de identidade convém restringir `CORS_ORIGINS` ao domínio real.
4. **Histórico em volume.** `api-data` continua SQLite local; em VPS, backup é opcional — perda do volume só apaga resumos anônimos (impacto baixo, decisão aceitável para MVP).
5. **Segredos.** `LLM_API_KEY`/`.env` entram como variáveis do host/compose — nunca na imagem nem no repo.

## 3. Escopo proposto

**Dentro:**
- VPS Linux (ex.: Oracle Cloud free tier) com Docker + Compose já existentes — sem mudança de arquitetura.
- Reverse proxy na frente com TLS automático: **Caddy** (HTTPS em ~5 linhas de config) — alternativa: Traefik ou Nginx+Certbot.
- Rate limit no endpoint `/api/scan` (ex.: 5/min por IP, 20/dia por cookie — números a calibrar) implementado no reverse proxy ou na API.
- `APP_ENV=production` já exige proxy de egress (Sprint 12); adicionar `Secure` no cookie e `CORS_ORIGINS` restrito ao domínio.
- Healthcheck externo + restart automático (`unless-stopped` já existe).
- Registro DNS do domínio escolhido pelo usuário.

**Fora (explícito):**
- Multi-instância, balanceador, Kubernetes, banco gerenciado — overkill para o modelo.
- CDN/WAF pago, contas, billing, telemetria/observabilidade gerenciada.
- Backup do volume `api-data` (aceito perder resumos anônimos; pode ser adicionado depois).
- Mudança nas regras de detecção ou no contrato além do rate limit.

## 4. Requisitos (testáveis)

1. `https://<domínio>/api/health` responde `200` com TLS válido e `HSTS`.
2. Scan público conclui para URL externa permitida; scan para `127.0.0.1`/`169.254.x`/RFC1918 segue `SSRF_BLOCKED` no servidor de produção.
3. A 6ª requisição `/api/scan` em <60 s do mesmo IP retorna `429` documentado no contrato.
4. `rastro_hid` chega ao navegador com `Secure; HttpOnly; SameSite=Lax`.
5. Saída direta da API para a internet permanece bloqueada (o egress passa só pelo Squid) — reexecutar a verificação de egress da Sprint 12 no servidor.
6. `docker compose down && up -d` mantém o histórico (volume nomeado) — já validado localmente.
7. Contrato v0.6 documenta `429` de rate limit e o cookie `Secure` em produção.

## 5. Dependências, restrições e suposições

- **Externas:** domínio (custo ~R$40/ano ou subdomínio gratuito — decisão do usuário), VPS com IP público e portas 80/443 liberadas no security list da Oracle.
- **Internas:** implementar rate limit (fastapi-limiter in-memory ou regra no Caddy — Caddy faz rate limit só via plugin; provável implementação na API com contador em memória).
- **Suposições (a testar):** tráfego baixo cabe no free tier (1 GB RAM — Chromium é pesado; pode exigir shape maior ou limite de scans concorrentes); IP de VPS residencial/datacenter não é bloqueado por mais sites que o residencial (conhecido: muitos sites bloqueiam datacenter).
- **Restrição real:** a Sprint 12 já alerta que alguns destinos bloqueiam datacenter — o score de sucesso de scans públicos em VPS pode ser menor que no IP residencial atual.

## 6. Métricas de sucesso

- Usuário externo consegue colar uma URL e ver o relatório em < 30 s sem nenhum passo extra.
- Nenhum scan consegue sair do proxy (verificação de egress reexecutada em produção).
- Rate limit segurando abuso simples sem afetar uso normal.

## 7. Fatias sugeridas (quando autorizado)

1. **15.2** — ✅ concluída em 2026-10-19: rate limit na API + `Secure` condicional no cookie + testes (`test_history.py` estendido, 22/22).
2. **15.3** — provisionar VPS, DNS e Caddy; deploy autorizado; reexecutar verificação de egress + smoke público.
3. **15.4** — contrato v0.6 + documentação de operação (logs, restart, rollback).
