# RASTRO - Setup e Credenciais

Este documento detalha o que o usuário (você) precisa configurar. **Nenhum agente Antigravity deve pedir senhas diretamente no chat.**

## O Que Você Precisa Fornecer

| Item | Quando será necessário? | Onde configurar? | Alternativa Gratuita Confirmada? |
| --- | --- | --- | --- |
| **Github (Acesso Local)** | Imediatamente (Sprint 1) | Seu terminal (`git login`). O agente apenas prepara os commits locais. | Sim (GitHub Free). |
| **Ambiente Python/Node** | Sprint 6 e Sprint 8 | Seu PC. O agente vai instruir como criar o `venv` e instalar o Playwright. | Sim. |
| **Chave de API Gemini** | Para testar a etapa semântica com Gemini 3.8 Flash | Arquivo `.env` local (nunca no chat ou no GitHub): `LLM_API_KEY`. A IA fica desligada até `LLM_ENABLED=true`. | O Google oferece cota gratuita sujeita a limites; na faixa gratuita, conteúdo pode ser usado para melhoria dos produtos e revisão humana. |
| **Acesso Oracle Cloud (VPS)**| Apenas no **Deploy** (Sprint 17)| Você criará as chaves SSH na sua máquina e configurará a infra. | Sim (Oracle Free Tier). |
| **Domínio e DNS** | Opcional (Futuro) | No painel do provedor de domínio apontando para o IP da VPS. | Não (domínios pagos). |

## Regras Estritas de Segurança (Para o Agente)
1. **NUNCA** faça commit do arquivo `.env`. Garanta que ele esteja no `.gitignore`.
2. **NUNCA** imprima valores de variáveis de ambiente no chat ou nos logs do sistema.
3. Se o Agente precisar verificar se uma chave existe, ele usará um script que responde `true` ou `false` em vez de mostrar a chave.
4. Qualquer URL fornecida pelo usuário no frontend da aplicação deve ser considerada hostil e barrada de tentar acessar IPs internos do servidor (SSRF) usando o pacote Playwright.

## Configuração local do Gemini 3.8 Flash

A chamada direta à API Gemini 3.8 Flash foi validada. A configuração da aplicação permanece desligada por padrão. Quando habilitada, o backend envia somente texto limitado da página e sinais textuais de controles, sem HTML bruto; em Docker, usa o proxy de egress existente. O plano gratuito do Google permite uso dos dados enviados para melhoria de produtos e revisão humana. Nunca envie a chave no chat nem coloque seu valor real no `.env.example`.

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

O scraper aguarda SCRAPER_RENDER_WAIT_MS=1800 ms após DOMContentLoaded para dar tempo à hidratação de SPAs. Ajuste entre 0 e 5.000 ms se necessário. A etapa semântica considera até 12.000 caracteres de texto visível; páginas que bloqueiam o bot ou mantêm conteúdo atrás de login ainda podem retornar pouco texto.

O Qwen via DashScope continua disponível com `LLM_PROVIDER=qwen`, `LLM_MODEL=qwen3.8-flash`, `LLM_BASE_URL=https://maas.qwencloudapi.com/compatible-mode/v1` e `LLM_API_KEY` (ou a variável legada `DASHSCOPE_API_KEY`). A tentativa pelo Docker chegou ao Gemini, mas terminou em APITimeoutError com o limite antigo de 12 segundos; após a atualização para 30 segundos, ainda é necessário confirmar uma análise híbrida bem-sucedida. Timeout, erro de configuração ou falha do provedor deixam a análise determinística disponível.
