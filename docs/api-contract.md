# RASTRO — Contrato implementado da API

> **Versão:** 0.6
> **Atualizado em:** 2026-10-19
> **Estado:** descreve o comportamento implementado em `backend/main.py`, incluindo a chamada semântica opcional via provedor compatível com OpenAI e o histórico anônimo local (sem contas).

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

O campo `url` é uma string com limite de 2.048 caracteres. O backend remove espaços nas pontas, rejeita entradas acima do limite e acrescenta `https://` quando o valor não começa com `http://` ou `https://`; a URL normalizada também precisa respeitar o limite. A rejeição ocorre na validação do request, antes da verificação anti-SSRF e da abertura do navegador.

O endpoint tem **rate limit por IP de origem**: no máximo `SCAN_RATE_LIMIT_PER_MINUTE` análises por minuto (padrão 10, em memória — uma janela deslizante por instância). O limite é avaliado antes de qualquer I/O; ao estourar, retorna `429` com `detail.code = "RATE_LIMIT"` sem abrir o navegador. A interface aplica a mesma validação para mostrar uma mensagem imediata e também exibe erros `422` de validação retornados pela API; o limite do backend é a proteção autoritativa.

Na resposta de sucesso, `url` é a URL solicitada e `domain` é o domínio da página final carregada, depois de redirects. Eles podem diferir. A interface e os relatórios locais usam `domain` para identificar o conteúdo efetivamente analisado; o endereço completo não é salvo no histórico nem no Markdown.

O Playwright carrega a página e observa mudanças no texto visível/DOM após `DOMContentLoaded`. A espera adaptativa usa por padrão um teto de 3.500 ms, espera no mínimo 2.000 ms e encerra após 750 ms sem mudanças ou ao atingir o teto (configurável por `SCRAPER_RENDER_WAIT_MS`, limitado a 0–5.000 ms; zero desativa a espera). Não aguarda `networkidle`. Depois da janela, o destino final é revalidado antes da extração. Em seguida, o analisador determinístico examina o DOM/texto. Se LLM_ENABLED=true e a chave estiver configurada, uma etapa opcional envia ao provedor escolhido (Gemini ou Qwen) até 12.000 caracteres de texto visível e sinais de controles da página, em payload limitado a 16.000 caracteres. HTML bruto não é enviado. A chamada do LLM usa timeout padrão de 30 segundos (LLM_TIMEOUT_SECONDS); em Docker, sai pelo proxy de egress. Se o modelo estiver desativado, sem chave ou indisponível, a API mantém o resultado determinístico. No plano gratuito do Gemini, o provedor pode usar entradas e respostas para melhorar produtos e permitir revisão humana; não envie conteúdo sensível.

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
      "evidence": "\"Restam 2 unidades\"",
      "dom_reference": "html:nth-of-type(1) > body:nth-of-type(1) > main:nth-of-type(1) > span:nth-of-type(2)",
      "phase": 1,
      "engine": "deterministic"
    }
  ],
  "meta": {
    "phase": 1,
    "engine": "deterministic",
    "llm_status": "disabled",
    "llm_unavailable_reason": null,
    "duration_ms": 1840,
    "rules_applied": 7,
    "dom_elements_scanned": 347,
    "visible_text_characters": 1280
  }
}
```

`findings[].dom_reference` é uma string opcional (`null` quando não há correspondência segura). Quando existe, contém um caminho posicional (`tag:nth-of-type(n)`) até um elemento do HTML capturado que contém o trecho citado na evidência. O caminho não inclui IDs, classes, atributos nem texto da página. Ele é específico daquela captura: a estrutura pode mudar entre acessos, e a referência não confirma que o elemento estava visível nem prova a interpretação do achado. Consumidores devem ignorar o campo quando ausente ou `null`.

`meta.visible_text_characters` é a quantidade de caracteres do `body.innerText` capturado depois de aparar espaços nas extremidades. É uma medida de volume, não de qualidade nem de texto efetivamente enviado ao LLM: o envio semântico continua sujeito ao limite de 12.000 caracteres e às demais regras do payload. O número pode aparecer no resultado e nos relatórios locais; o texto da página não é armazenado nesses relatórios.

Quando a etapa semântica termina com sucesso, `meta.phase` é `2`, `meta.engine` é `hybrid`, e findings produzidos pelo modelo têm `phase: 2` e `engine: "llm"`. `meta.llm_status` pode ser `disabled`, `ok`, `skipped` (sem conteúdo útil para enviar) ou `unavailable`. Em `unavailable`, a resposta continua `200 OK` e contém o resultado determinístico. `meta.llm_unavailable_reason` é `null` quando não se aplica; em caso de indisponibilidade, contém apenas uma categoria segura: `not_configured`, `configuration_error`, `timeout`, `rate_limited`, `authentication_error`, `network_error`, `request_rejected`, `invalid_response` ou `provider_error`. O campo nunca contém corpo de erro do provedor, chave, URL ou texto da página. `duration_ms` mede o tempo total da requisição de análise.

`score` é a soma dos pesos por severidade (`critical=30`, `high=20`, `medium=10`, `low=5`), limitada a 100. Quando o LLM está ativo, findings determinísticos e semânticos contribuem para a mesma soma. É um indicador heurístico não calibrado; não representa probabilidade estatística nem prova de intenção.

| Faixa do score | `risk_level` |
|---:|---|
| 0–24 | `low` |
| 25–49 | `medium` |
| 50–74 | `high` |
| 75–100 | `critical` |

As sete regras atualmente registradas são `fake_scarcity`, `fake_urgency`, `confirmshaming`, `price_anchoring`, `hidden_preselection`, `dark_overlay` e `consent_asymmetry`. Na regra de urgência, classes CSS de contadores só contam quando o Playwright confirma elemento visível e valor temporal; termos isolados como “timer” não bastam. Chamadas textuais vagas para agir logo (“corra”, “hurry”, “apresse-se”, “act now”) são sinais médios de urgência, enquanto “acabando” isolado não basta para escassez. `fake_scarcity` exige quantidade ou referência contextual explícita a estoque, disponibilidade, itens, vagas ou oferta limitada, e opera sobre até 500 trechos curtos de elementos renderizados pelo Playwright. Texto de elementos ou ancestrais ocultos por `display:none`, `visibility:hidden`, opacidade muito baixa, `hidden` ou `aria-hidden=true` é descartado; o mesmo acontece com trechos posicionados totalmente fora da tela em coordenadas negativas, enquanto conteúdo renderizado abaixo da dobra continua elegível. A mesma lista de candidatos renderizados alimenta `confirmshaming` e a variante textual de `fake_urgency`, que também só pontuam trechos de elementos renderizados. `price_anchoring` exige um preço antigo renderizado (`del`, `s`, `strike` ou classe de preço antigo) e um preço atual distinto no mesmo contexto compacto. Os trechos intermediários não são enviados ao LLM nem persistidos. A regra de pré-seleção exige checkbox marcado no estado atual, rótulo associado visível e texto relacionado a marketing/newsletter/oferta; checkbox sem rótulo não é evidência suficiente. A regra de consentimento só sinaliza a falta de recusa direta na primeira camada ou um destaque visual muito maior para aceitar do que para recusar. Um banner equilibrado não soma pontos apenas por existir. `findings` pode ser vazio. `meta.rules_applied` é a quantidade de regras registradas, não a quantidade de achados.

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
| `404` | Item de histórico inexistente ou de outra identidade | `detail` contém `code: "HISTORY_NOT_FOUND"`. |
| `429` | Rate limit de análise excedido para o IP | `detail` contém `code: "RATE_LIMIT"`. |
| `503` | Falha ou indisponibilidade do scraper | `detail` contém os campos do erro do scanner. |
| `500` | Erro não tratado | Resposta padrão de erro do FastAPI/Uvicorn. |

A página de destino bloqueada por anti-bot (`403`/`429` devolvidos pelo site) continua saindo como `403` do scanner — distinta do `429` de rate limit do próprio RASTRO. Também não há tratamento customizado `415`.

### Histórico anônimo (sem contas)

O RASTRO identifica o navegador por um cookie opaco `rastro_hid` (32 caracteres hex, `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age` de 1 ano; a flag `Secure` é emitida quando `APP_ENV=production` — navegadores tratam loopback como origem confiável, então o Docker local continua funcionando sobre HTTP), emitido na primeira resposta bem-sucedida da API quando ausente ou inválido. Não há cadastro, login nem dado pessoal: o cookie é apenas um identificador aleatório. Perder ou apagar o cookie torna o histórico anterior inacessível.

Todo `/api/scan` bem-sucedido grava automaticamente um **resumo** vinculado a essa identidade: domínio final, domínio solicitado, data, score, risco, achados (tipo, evidência limitada a 240 caracteres, referência de DOM, severidade, motor) e metadados de execução. URL completa, HTML e texto integral da página **não são persistidos**. A retenção é de no máximo 100 resumos por identidade — os mais antigos são descartados. A gravação é best-effort: falha de banco não altera a resposta do scan.

```http
GET /api/history
```

Resposta `200 OK`:

```json
{
  "items": [
    {
      "id": "9f1c...32hex",
      "scannedAt": "2026-10-19T18:00:00+00:00",
      "domain": "exemplo.com",
      "requestedDomain": "exemplo.com",
      "score": 20,
      "riskLevel": "low",
      "scanEngine": "deterministic",
      "llmStatus": "disabled",
      "llmUnavailableReason": null,
      "durationMs": 1840,
      "domElementsScanned": 347,
      "visibleTextCharacters": 1280,
      "rulesApplied": 7,
      "findings": [
        { "id": "fake_scarcity", "type": "Falsa escassez", "evidence": "Restam 2 unidades", "domReference": null, "severity": "high", "engine": "deterministic" }
      ]
    }
  ],
  "limit": 100
}
```

```http
DELETE /api/history/{item_id}
DELETE /api/history
```

Removem um item ou todo o histórico **somente da identidade do cookie**; ambos retornam `204 No Content`. Item inexistente ou de outra identidade retorna `404` com `detail.code = "HISTORY_NOT_FOUND"`. O banco é um arquivo SQLite local (`RASTRO_DB_PATH`, volume `api-data` no Compose); não há sincronização entre instalações.

## CORS e configuração

`CORS_ORIGINS` configura as origens, separadas por vírgula. O valor padrão do código é `*`; `.env.example` sugere `http://localhost:8000`. Métodos aceitos pelo middleware: `GET`, `POST` e `OPTIONS`; header permitido: `Content-Type`.

## Limitações do contrato atual

- O provedor pode estar indisponível ou produzir uma interpretação incompleta; os findings semânticos são limitados a quatro e só entram na resposta se a evidência retornada aparecer literalmente no recorte enviado. Isso reduz citações inventadas, mas não valida a interpretação do modelo.
- A API não tem autenticação, endpoint de download de relatório nem rate limiting. O histórico anônimo é vinculado ao cookie `rastro_hid` e fica no SQLite da instalação; quem tiver acesso ao cookie vê os resumos dessa identidade. A interface web gera downloads Markdown no próprio navegador e não sincroniza entre dispositivos nem instalações.
- Códigos e mensagens exatos de exceções de validação podem variar com a versão do FastAPI/Pydantic; consumidores devem usar o status HTTP e tratar os formatos documentados sem depender de texto específico.
- A checagem anti-SSRF da aplicação é defesa em profundidade. O modo Docker com egress controlado está documentado separadamente e ainda exige validação operacional antes de exposição pública.
