# RASTRO - Setup e Credenciais

Este documento detalha o que o usuário (você) precisa configurar. **Nenhum agente Antigravity deve pedir senhas diretamente no chat.**

## O Que Você Precisa Fornecer

| Item | Quando será necessário? | Onde configurar? | Alternativa Gratuita Confirmada? |
| --- | --- | --- | --- |
| **Github (Acesso Local)** | Imediatamente (Sprint 1) | Seu terminal (`git login`). O agente apenas prepara os commits locais. | Sim (GitHub Free). |
| **Ambiente Python/Node** | Sprint 6 e Sprint 8 | Seu PC. O agente vai instruir como criar o `venv` e instalar o Playwright. | Sim. |
| **Chave de API LLM** | Apenas na **Fase 2** (Sprint 18) | Arquivo `.env` local (nunca no chat ou no GitHub). Ex: `OPENROUTER_API_KEY`. | Sim (Ollama local ou tier free OpenRouter/Google AI Studio). |
| **Acesso Oracle Cloud (VPS)**| Apenas no **Deploy** (Sprint 17)| Você criará as chaves SSH na sua máquina e configurará a infra. | Sim (Oracle Free Tier). |
| **Domínio e DNS** | Opcional (Futuro) | No painel do provedor de domínio apontando para o IP da VPS. | Não (domínios pagos). |

## Regras Estritas de Segurança (Para o Agente)
1. **NUNCA** faça commit do arquivo `.env`. Garanta que ele esteja no `.gitignore`.
2. **NUNCA** imprima valores de variáveis de ambiente no chat ou nos logs do sistema.
3. Se o Agente precisar verificar se uma chave existe, ele usará um script que responde `true` ou `false` em vez de mostrar a chave.
4. Qualquer URL fornecida pelo usuário no frontend da aplicação deve ser considerada hostil e barrada de tentar acessar IPs internos do servidor (SSRF) usando o pacote Playwright.
