# Estado do Projeto RASTRO

*Este arquivo deve ser atualizado pelo agente Antigravity no final de cada sprint para manter o contexto vivo caso a sessão caia ou o limite de tokens seja alcançado.*

- **Data da Última Atualização**: 2026-09-26
- **Sprint Atual/Concluída**: **Sprint 13 concluída; análise híbrida confirmada pelo usuário**. Próxima proposta: microsprint de qualidade para investigar falsos positivos, aguardando aprovação antes de iniciar.
- **Fase**: MVP local com análise determinística e etapa semântica Gemini funcional no Docker. O usuário confirmou análise híbrida real em mercadolivre.com.br. A interface continua preservando fallback determinístico.

## O Que Foi Entregue (MVP Completo)
1. **Frontend Completo e Integrado**: `frontend/index.html` consumindo a API verdadeira e demonstrando resultados (Score, Risco, Elementos lidos e Findings) dinamicamente com base em dados de varreduras reais.
2. **Backend API Robusto**: FastAPI (`backend/main.py`) servindo endpoints e páginas estáticas. Inclui configuração dedicada para subprocessos no Windows via `run_server.py`.
3. **Filtro de Destino**: `backend/security.py` valida a URL inicial e `backend/scraper.py` intercepta requests HTTP(S) no contexto do navegador. Isso é defesa em profundidade, não uma garantia de isolamento.
4. **Scraping Real (Playwright)**: `backend/scraper.py` aplica timeout, bloqueia recursos pesados e service workers e filtra destinos não públicos em requests interceptados.
5. **Motor Determinístico de Dark Patterns**: `backend/analyzer.py` possui 6 regras de negócio estruturadas (Urgência, Escassez, Confirmshaming, Ancoragem, Pré-seleção e Overlay).
6. **Sprint 12 — Isolamento de egress validado**: `compose.yaml` separa API e proxy por rede interna; firewall da API só permite loopback, DNS interno e proxy; firewall do proxy restringe portas e bloqueia destinos não públicos/IPv6; API exige proxy em `APP_ENV=production`; porta publicada fica em `127.0.0.1:8000`. O usuário confirmou os critérios de rede, redirects, usuários dos processos, scans após reinício e bloqueio de saída direta.
7. **Sprint 13 — análise semântica opcional**: concluída e validada em Docker. O usuário observou “Análise híbrida” e conclusão em 13.161 ms numa análise do Mercado Livre. A implementação envia texto limitado, trata conteúdo da página como não confiável, valida citações e mantém fallback determinístico; usa Gemini 3.8 Flash, espera de renderização configurável de 1.800 ms e contexto semântico de até 12.000 caracteres. A validação manual identificou possível falso positivo na regra de overlay: evidência “Pular para o conteúdo Comentar”, provavelmente link de acessibilidade.

## Instruções Atuais de Uso (Runbook)
Para rodar a versão final do MVP:
```powershell
.venv\Scripts\activate
python run_server.py
```
- Acesse `http://localhost:8000` para testar o painel visual e analisar URLs reais.
- Acesse `http://localhost:8000/docs` para visualizar a documentação oficial da API (Swagger UI).

## Próximos Passos (Backlog - Fases Futuras)
- **Próximo passo proposto — qualidade dos achados**: revisar o falso positivo de overlay observado no Mercado Livre e testar páginas controle/páginas com pop-ups reais. A regra atual considera qualquer role=dialog como overlay intrusivo; melhorar a evidência de visibilidade antes de classificar. Esta microsprint ainda requer aprovação.
- **Banco de Dados & Relatórios**: Criar banco SQL/NoSQL para manter histórico de análises por data e permitir exportação de relatório.
- **Deploy em Nuvem**: Mover para um ambiente de produção (VPS Linux, Docker, orquestração).

## Restrições ou Problemas Conhecidos Atuais
- **Sprint 12 concluída em Docker local**: scans públicos funcionaram; saída direta para `1.1.1.1:443` permaneceu `BLOQUEADO` após restart; loopback, hostname Docker interno, RFC1918, link-local/metadata e IPv4 mapeado em IPv6 retornaram `SSRF_BLOCKED_IP`; redirect controlado para example.com concluiu, enquanto o redirect para loopback retornou `ACCESS_BLOCKED` sem relatório. Após `docker compose restart`, os serviços voltaram `healthy` e o scan público continuou funcionando. `docker compose top` confirmou Uvicorn como UID 1000 (`pwuser`) e Squid como `proxy` (UID 13); configuração usa `chromium_sandbox=True` e seccomp customizado sem `--no-sandbox`.
- **Resultados inconclusivos**: as tentativas com `httpbingo.org` no RASTRO e `httpbin.io` via curl retornaram HTTP 403 antes de confirmar um redirect válido. Na segunda tentativa, o parâmetro também foi colado como texto de link Markdown, não como URL literal; nenhuma delas valida ou reprova a proteção contra redirects.
- **Redirect confirmado na origem**: `httpbin.dev/redirect-to` respondeu `302 Found` via curl e enviou `Location` para `http://127.0.0.1/`; o parâmetro foi montado por variáveis no CMD. Isso confirma o servidor de teste, mas ainda não comprova como o RASTRO lida com a navegação.
- **Controle público aprovado**: o RASTRO concluiu a análise após seguir `httpbin.dev/redirect-to` até `https://example.com/` (resposta `status: ok`, domínio final `example.com`). Isso confirma que o endpoint e a cadeia de redirect funcionam no Chromium do RASTRO.
- **Redirect privado bloqueado**: com a mesma origem e mesma cadeia, mudar o destino para `http://127.0.0.1/` retornou `ACCESS_BLOCKED` (HTTP 403), sem relatório. Como o controle para example.com concluiu e o endpoint anunciou `Location` para loopback, o resultado é evidência de que a navegação privada foi recusada.
- **Reinício e egress pós-restart**: `docker compose restart` trouxe API e egress-proxy de volta como `healthy`; `https://example.com/` retornou `status: ok`; tentativa direta da API para `1.1.1.1:443` retornou `BLOQUEADO`.
- **Usuários e sandbox**: `docker compose top` mostrou Uvicorn como UID 1000 (`pwuser`) e Squid como usuário `proxy` (UID 13); `docker-init` aparece como root no bootstrap. O scraper usa `chromium_sandbox=True`, Compose aplica perfil seccomp customizado e não há `--no-sandbox` nos argumentos; análises concluídas confirmam inicialização do Chromium.
- **Próxima etapa**: iniciar a microsprint de qualidade somente após aprovação explícita; não iniciar deploy nem persistência antes de planejar suas próprias microsprints.
- **Pontuação heurística**: o score soma pesos de regras e não é uma probabilidade calibrada de manipulação nem prova de intenção.
- O código original legado da extensão Chrome (arquivos na raiz como manifest e popups) não tem mais serventia, o foco mudou 100% para a plataforma Web SaaS.
- A máquina Windows local exige a flag `loop="none"` e uso da `WindowsProactorEventLoopPolicy` para que a integração Uvicorn + Playwright funcione adequadamente, garantido pelo `run_server.py`.
