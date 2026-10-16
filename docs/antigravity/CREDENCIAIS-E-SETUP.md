# RASTRO - Setup e Credenciais

Este documento detalha o que o usuário (você) precisa configurar. **Nenhum agente Antigravity deve pedir senhas diretamente no chat.**

## O Que Você Precisa Fornecer

| Item | Quando será necessário? | Onde configurar? | Alternativa Gratuita Confirmada? |
| --- | --- | --- | --- |
| **Github (Acesso Local)** | Imediatamente (Sprint 1) | Seu terminal (`git login`). O agente apenas prepara os commits locais. | Sim (GitHub Free). |
| **Docker Desktop** | Para subir e usar o MVP com o isolamento de egress local | Inicie o Docker Desktop e, na raiz do projeto, use `docker compose up -d --build api`. Consulte o runbook no `README.md`. | Sim, Docker Desktop é gratuito para uso pessoal. |
| **Ambiente Python** | Somente para a execução alternativa sem Docker | Seu PC. O script `run_server.py` inicia a aplicação após instalar os requisitos e o Chromium do Playwright. | Sim. Esse modo não tem o isolamento de egress do Compose. |
| **Chave de API Gemini** | Para habilitar a etapa semântica com Gemini 3.8 Flash | Arquivo `.env` local (nunca no chat ou no GitHub): `LLM_API_KEY`. O Compose deixa o LLM desligado por padrão; configure `LLM_ENABLED=true` para ativá-lo. O caminho híbrido foi confirmado no Docker local. | O Google oferece cota gratuita sujeita a limites; na faixa gratuita, conteúdo pode ser usado para melhoria dos produtos e revisão humana. |
| **Acesso Oracle Cloud (VPS)**| Apenas no **Deploy** (Sprint 17)| Você criará as chaves SSH na sua máquina e configurará a infra. | Sim (Oracle Free Tier). |
| **Domínio e DNS** | Opcional (Futuro) | No painel do provedor de domínio apontando para o IP da VPS. | Não (domínios pagos). |

## Regras Estritas de Segurança (Para o Agente)
1. **NUNCA** faça commit do arquivo `.env`. Garanta que ele esteja no `.gitignore`.
2. **NUNCA** imprima valores de variáveis de ambiente no chat ou nos logs do sistema.
3. Se o Agente precisar verificar se uma chave existe, ele usará um script que responde `true` ou `false` em vez de mostrar a chave.
4. Qualquer URL fornecida pelo usuário no frontend da aplicação deve ser considerada hostil e barrada de tentar acessar IPs internos do servidor (SSRF) usando o pacote Playwright.

## Configuração local do Gemini 3.8 Flash

O fluxo híbrido com Gemini 3.8 Flash foi confirmado na aplicação dentro do Docker. No Compose, a integração continua desligada por padrão e só é ativada quando as variáveis são configuradas. Quando habilitada, o backend envia texto limitado da página e sinais textuais de controles, sem HTML bruto, usando o proxy de egress. O plano gratuito do Google permite uso dos dados enviados para melhoria de produtos e revisão humana. Nunca envie a chave no chat nem coloque seu valor real no `.env.example`.

```dotenv
LLM_ENABLED=true
LLM_PROVIDER=gemini
LLM_API_KEY=COLOQUE_SUA_CHAVE_APENAS_NO_ARQUIVO_ENV_LOCAL
LLM_MODEL=gemini-3.8-flash
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_TIMEOUT_SECONDS=30
```

Após editar `.env` para Docker, recrie a API para ela ler a configuração:

```powershell
docker compose up -d --build api
```

O scraper observa mudanças no texto/DOM após `DOMContentLoaded`: espera no mínimo 2.000 ms e encerra após 750 ms sem mudanças, respeitando o teto de `SCRAPER_RENDER_WAIT_MS` (padrão 3.500 ms; ajuste de 0 a 5.000 ms, sendo 0 a desativação). Não espera `networkidle`. A etapa semântica considera até 12.000 caracteres de texto visível; páginas que bloqueiam o bot ou mantêm conteúdo atrás de login ainda podem retornar pouco texto.

O backend também mantém um adaptador compatível com Qwen via DashScope, mas a integração validada neste MVP é Gemini. Para trocar de provedor, configure as variáveis locais conforme o modelo escolhido e reconstrua a API; não mantenha chaves no código-fonte. Timeout, erro de configuração ou falha do provedor deixam a análise determinística disponível.
