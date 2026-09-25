# RASTRO — Contrato da API

> **Status:** Definido · **Versão:** 0.1 · **Fase:** Sprint 5 (sem implementação de backend)

Este documento é a fonte de verdade do contrato HTTP entre o `frontend/` e o `backend/`.  
Qualquer alteração aqui deve ser aprovada antes de ser implementada.

---

## Endpoint único (MVP)

```
POST /api/scan
Content-Type: application/json
```

---

## Request

```json
{
  "url": "https://exemplo.com/pagina"
}
```

| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `url` | `string` | ✅ | Protocolo `http` ou `https`. Hostname público (não-IP, não-localhost em produção). Máx. 2048 chars. |

---

## Respostas de Sucesso

### `200 OK` — Análise concluída

```json
{
  "status": "ok",
  "url": "https://exemplo.com/pagina",
  "domain": "exemplo.com",
  "scanned_at": "2026-09-25T17:00:00Z",
  "score": 72,
  "risk_level": "high",
  "findings": [
    {
      "id": "fake_scarcity",
      "type": "Falsa escassez",
      "severity": "high",
      "evidence": "\"Restam apenas 2 unidades\"",
      "phase": 1,
      "engine": "deterministic"
    },
    {
      "id": "confirmshaming",
      "type": "Indução à culpa",
      "severity": "medium",
      "evidence": "\"Não, prefiro perder a oferta\"",
      "phase": 1,
      "engine": "deterministic"
    }
  ],
  "meta": {
    "phase": 1,
    "engine": "deterministic",
    "duration_ms": 1240,
    "rules_applied": 12,
    "dom_elements_scanned": 347
  }
}
```

#### Campos da resposta raiz

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | `"ok"` | Sempre `"ok"` neste cenário |
| `url` | `string` | URL normalizada analisada |
| `domain` | `string` | Hostname sem `www.` |
| `scanned_at` | `string (ISO 8601)` | Timestamp UTC da análise |
| `score` | `integer (0–100)` | Score de risco agregado |
| `risk_level` | `"low" \| "medium" \| "high" \| "critical"` | Classificação textual do score |
| `findings` | `Finding[]` | Array de achados (pode ser vazio `[]`) |
| `meta` | `object` | Metadados internos da análise |

#### Thresholds de `risk_level`

| Score | `risk_level` | Label exibido no frontend |
|---|---|---|
| 0–24 | `"low"` | risco baixo |
| 25–49 | `"medium"` | risco moderado |
| 50–74 | `"high"` | risco elevado |
| 75–100 | `"critical"` | risco crítico |

#### Campos do objeto `Finding`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `string` | Identificador interno da regra (snake_case) |
| `type` | `string` | Nome legível do padrão detectado |
| `severity` | `"low" \| "medium" \| "high" \| "critical"` | Gravidade do achado |
| `evidence` | `string` | Trecho de texto ou descrição do elemento detectado |
| `phase` | `1 \| 2` | Fase de detecção: `1` = determinístico, `2` = LLM |
| `engine` | `"deterministic" \| "llm"` | Motor que gerou o achado |

---

## Respostas de Erro

### `422 Unprocessable Entity` — URL inválida (validação antes do scraping)

```json
{
  "status": "error",
  "code": "INVALID_URL",
  "message": "A URL fornecida não é válida ou não usa protocolo HTTP/HTTPS.",
  "detail": null
}
```

### `503 Service Unavailable` — Página inacessível (scraping falhou)

```json
{
  "status": "error",
  "code": "PAGE_UNREACHABLE",
  "message": "Não foi possível acessar a página. Verifique se o endereço está correto e acessível publicamente.",
  "detail": "timeout após 15000ms"
}
```

> **Nota:** Este é o cenário simulado no frontend com ~25% de probabilidade.

### `403 Forbidden` — Bloqueado por anti-bot (Cloudflare, Datadome, etc.)

```json
{
  "status": "error",
  "code": "ACCESS_BLOCKED",
  "message": "A página bloqueou o acesso automatizado. O RASTRO não tenta bypassar proteções anti-bot.",
  "detail": "HTTP 403 recebido do servidor de destino"
}
```

### `429 Too Many Requests` — Rate limit da API RASTRO

```json
{
  "status": "error",
  "code": "RATE_LIMIT",
  "message": "Muitas requisições. Aguarde antes de enviar outra URL.",
  "detail": "retry_after_seconds: 30"
}
```

### `500 Internal Server Error` — Erro inesperado no backend

```json
{
  "status": "error",
  "code": "INTERNAL_ERROR",
  "message": "Ocorreu um erro interno. Tente novamente em instantes.",
  "detail": null
}
```

---

## Catálogo de `id` de findings (Fase 1 — determinístico)

Regras planejadas para a Sprint 9:

| `id` | `type` | Método de detecção |
|---|---|---|
| `fake_scarcity` | Falsa escassez | Regex em texto de botões/badges |
| `fake_urgency` | Urgência fabricada | Regex + detecção de countdown |
| `confirmshaming` | Indução à culpa | Regex em textos de recusa |
| `price_anchoring` | Ancoragem de preço | CSS selector em preços riscados |
| `hidden_preselection` | Pré-seleção oculta | Atributo `checked` em inputs ocultos |
| `roach_motel` | Roach motel | Comparação de fluxo assimétrico |
| `dark_overlay` | Dark overlay | Detecção de modais com z-index alto |
| `nagging` | Nagging | Contagem de modais por sessão |

---

## Notas de implementação (para Sprint 6+)

- O backend **não salva** resultados em banco de dados no MVP (stateless).
- O `score` é calculado como: `min(100, soma dos pesos de cada finding)` onde pesos variam por `severity`: `critical=30, high=20, medium=10, low=5`.
- O `Content-Type: application/json` é obrigatório no request; o backend retorna `415` caso contrário.
- CORS: em desenvolvimento, aceita `*`. Em produção, apenas o domínio configurado em `CORS_ORIGINS`.
