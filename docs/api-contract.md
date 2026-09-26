# RASTRO — Contrato implementado da API

> **Versão:** 0.3
> **Atualizado em:** 2026-09-26
> **Estado:** descreve o comportamento implementado em `backend/main.py`, incluindo a chamada semântica opcional via provedor compatível com OpenAI.

## Health check

```http
GET /api/health
```

Resposta `200 OK`:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development"
}
```

## Análise de URL

```http
POST /api/scan
Content-Type: application/json
```

Request:

```json
{
  "url": "https://exemplo.com/pagina"
}
```

O campo `url` é uma string. O backend remove espaços nas pontas e acrescenta `https://` quando o valor não começa com `http://` ou `https://`. Depois valida a estrutura e aplica a verificação anti-SSRF antes de abrir o navegador. O código não declara atualmente um limite próprio de 2.048 caracteres.

O Playwright carrega a página, aguarda por padrão 1.800 ms após DOMContentLoaded para permitir renderização/hidratação de SPAs (configurável por SCRAPER_RENDER_WAIT_MS, limitado a 0–5.000 ms) e então o analisador determinístico examina o DOM/texto. Se LLM_ENABLED=true e a chave estiver configurada, uma etapa opcional envia ao provedor escolhido (Gemini ou Qwen) até 12.000 caracteres de texto visível e sinais de controles da página, em payload limitado a 16.000 caracteres. HTML bruto não é enviado. A chamada do LLM usa timeout padrão de 30 segundos (LLM_TIMEOUT_SECONDS); em Docker, sai pelo proxy de egress. Se o modelo estiver desativado, sem chave ou indisponível, a API mantém o resultado determinístico. No plano gratuito do Gemini, o provedor pode usar entradas e respostas para melhorar produtos e permitir revisão humana; não envie conteúdo sensível.

### Sucesso — `200 OK`

```json
{
  "status": "ok",
  "url": "https://exemplo.com/pagina",
  "domain": "exemplo.com",
  "scanned_at": "2026-09-25T17:00:00+00:00",
  "score": 20,
  "risk_level": "low",
  "findings": [
    {
      "id": "fake_scarcity",
      "type": "Falsa escassez",
      "severity": "high",
      "evidence": "Restam 2 unidades",
      "phase": 1,
      "engine": "deterministic"
    }
  ],
  "meta": {
    "phase": 1,
    "engine": "deterministic",
    "llm_status": "disabled",
    "duration_ms": 1840,
    "rules_applied": 6,
    "dom_elements_scanned": 347
  }
}
```

Quando a etapa semântica termina com sucesso, `meta.phase` é `2`, `meta.engine` é `hybrid`, e findings produzidos pelo modelo têm `phase: 2` e `engine: "llm"`. `meta.llm_status` pode ser `disabled`, `ok`, `skipped` (sem conteúdo útil para enviar) ou `unavailable`. Em `unavailable`, a resposta continua `200 OK` e contém o resultado determinístico. `duration_ms` mede o tempo total da requisição de análise.

`score` é a soma dos pesos por severidade (`critical=30`, `high=20`, `medium=10`, `low=5`), limitada a 100. Quando o LLM está ativo, findings determinísticos e semânticos contribuem para a mesma soma. É um indicador heurístico não calibrado; não representa probabilidade estatística nem prova de intenção.

| Faixa do score | `risk_level` |
|---:|---|
| 0–24 | `low` |
| 25–49 | `medium` |
| 50–74 | `high` |
| 75–100 | `critical` |

As seis regras atualmente registradas são `fake_scarcity`, `fake_urgency`, `confirmshaming`, `price_anchoring`, `hidden_preselection` e `dark_overlay`. `findings` pode ser vazio. `meta.rules_applied` é a quantidade de regras registradas, não a quantidade de achados.

### Respostas de erro

Os erros lançados com `HTTPException` aparecem no corpo dentro de `detail`, como é padrão no FastAPI:

```json
{
  "detail": {
    "status": "error",
    "code": "SSRF_BLOCKED_IP",
    "message": "A URL aponta para um destino bloqueado.",
    "detail": null
  }
}
```

| HTTP | Caso implementado | Corpo |
|---:|---|---|
| `422` | Erro de validação do request | `detail` de validação padrão do FastAPI; a forma não é igual à dos erros do scanner. |
| `422` | Destino rejeitado pela validação anti-SSRF | `detail` contém `status`, `code`, `message` e `detail`. |
| `403` | Página devolveu `403` ou `429`, interpretada como bloqueio anti-bot | `detail` contém os campos do erro do scanner. |
| `503` | Falha ou indisponibilidade do scraper | `detail` contém os campos do erro do scanner. |
| `500` | Erro não tratado | Resposta padrão de erro do FastAPI/Uvicorn. |

Não há rate limit implementado no endpoint: `429` não é um erro emitido pelo controle de taxa do RASTRO. Também não há tratamento customizado `415`.

## CORS e configuração

`CORS_ORIGINS` configura as origens, separadas por vírgula. O valor padrão do código é `*`; `.env.example` sugere `http://localhost:8000`. Métodos aceitos pelo middleware: `GET`, `POST` e `OPTIONS`; header permitido: `Content-Type`.

## Limitações do contrato atual

- O provedor pode estar indisponível ou produzir uma interpretação incompleta; os findings semânticos são limitados a quatro e só entram na resposta se a evidência retornada aparecer literalmente no recorte enviado. Isso reduz citações inventadas, mas não valida a interpretação do modelo.
- Não há autenticação, persistência, histórico, download de relatório nem rate limiting.
- Códigos e mensagens exatos de exceções de validação podem variar com a versão do FastAPI/Pydantic; consumidores devem usar o status HTTP e tratar os formatos documentados sem depender de texto específico.
- A checagem anti-SSRF da aplicação é defesa em profundidade. O modo Docker com egress controlado está documentado separadamente e ainda exige validação operacional antes de exposição pública.
