"""
RASTRO — Backend API
Sprint 9: motor determinístico de detecção de dark patterns integrado.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse

# Patch obrigatório para rodar Playwright + FastAPI (Uvicorn) no Windows.
# O Playwright usa subprocessos, que exigem o ProactorEventLoopPolicy no Windows.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from backend import db
from backend.analyzer import ScanFinding, analyze, compute_score, find_evidence_dom_references, rules_count
from backend.llm_analyzer import analyze_semantically
from backend.scraper import ScraperError, fetch_page
from backend.security import SSRFError, check_ssrf

# ── Configuração ─────────────────────────────────────────────
load_dotenv()

APP_VERSION = "0.1.0"
APP_ENV     = os.getenv("APP_ENV", "development")
APP_PORT    = int(os.getenv("APP_PORT", "8000"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
MAX_URL_LENGTH = 2048
SCAN_RATE_LIMIT_PER_MINUTE = int(os.getenv("SCAN_RATE_LIMIT_PER_MINUTE", "10"))

# Janela deslizante em memória: scans por IP de origem (instância única).
_scan_hits: dict[str, list[float]] = {}

# ── Aplicação ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # O histórico é best-effort: uma falha de banco não impede a API de subir.
    try:
        db.init_db()
    except Exception:
        pass
    yield


app = FastAPI(
    title="RASTRO API",
    description=(
        "Scanner de dark patterns e copywriting manipulativo em páginas web. "
        "O endpoint `/api/scan` usa Playwright e regras determinísticas, com "
        "análise semântica opcional via provedor OpenAI-compatible quando configurada."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


# ── Schemas (alinhados ao docs/api-contract.md) ───────────────

class ScanRequest(BaseModel):
    """Requisição de análise de URL."""
    url: str

    @field_validator("url")
    @classmethod
    def normalise_and_validate(cls, v: str) -> str:
        v = v.strip()
        if len(v) > MAX_URL_LENGTH:
            raise ValueError("A URL deve ter no máximo 2.048 caracteres.")
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        if len(v) > MAX_URL_LENGTH:
            raise ValueError("A URL deve ter no máximo 2.048 caracteres.")
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL deve usar protocolo HTTP ou HTTPS.")
        if not parsed.netloc or "." not in parsed.netloc:
            raise ValueError("Hostname inválido ou ausente.")
        return v


class Finding(BaseModel):
    id: str
    type: str
    severity: str       # "low" | "medium" | "high" | "critical"
    evidence: str
    dom_reference: str | None = None  # positional path in the captured DOM, without page attributes
    phase: int          # 1 = determinístico | 2 = LLM
    engine: str         # "deterministic" | "llm"


class ScanMeta(BaseModel):
    phase: int
    engine: str
    llm_status: str       # "disabled" | "ok" | "skipped" | "unavailable"
    llm_unavailable_reason: str | None = None  # safe category; never provider details
    duration_ms: int
    rules_applied: int
    dom_elements_scanned: int
    visible_text_characters: int


class ScanResponse(BaseModel):
    status: str
    url: str
    domain: str
    scanned_at: str
    score: int
    risk_level: str     # "low" | "medium" | "high" | "critical"
    findings: list[Finding]
    meta: ScanMeta


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    status: str
    code: str
    message: str
    detail: str | None = None


# ── Helpers ───────────────────────────────────────────────────
def _ensure_owner(request: Request, response: Response) -> str:
    """Identidade anônima do navegador: cookie opaco, sem dados pessoais."""
    owner = request.cookies.get(db.COOKIE_NAME)
    if not db.is_owner_token(owner):
        owner = db.new_owner_token()
        response.set_cookie(
            db.COOKIE_NAME,
            owner,
            max_age=365 * 24 * 3600,
            httponly=True,
            samesite="lax",
            path="/",
            # Em produção o cookie só trafega por HTTPS. Navegadores tratam
            # loopback (127.0.0.1/localhost) como origem confiável, então o
            # modo Docker local continua funcionando sobre HTTP.
            secure=APP_ENV == "production",
        )
    return owner


def _enforce_scan_rate_limit(request: Request) -> None:
    """Janela deslizante de 60 s por IP de origem, em memória."""
    limit = SCAN_RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return
    client_ip = request.client.host if request.client else "local"
    now = time.monotonic()
    hits = [t for t in _scan_hits.get(client_ip, []) if now - t < 60]
    if len(hits) >= limit:
        _scan_hits[client_ip] = hits
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "status": "error",
                "code": "RATE_LIMIT",
                "message": "Muitas análises em sequência. Aguarde alguns instantes.",
                "detail": None,
            },
        )
    hits.append(now)
    _scan_hits[client_ip] = hits


def _score_to_risk_level(score: int) -> str:
    """Converte score numérico em label conforme contrato."""
    if score < 25:
        return "low"
    if score < 50:
        return "medium"
    if score < 75:
        return "high"
    return "critical"


# ── Rotas ─────────────────────────────────────────────────────

@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Sistema"],
    summary="Health check",
)
def health_check() -> HealthResponse:
    """Verifica se a API está no ar e retorna a versão."""
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        environment=APP_ENV,
    )


@app.post(
    "/api/scan",
    response_model=ScanResponse,
    tags=["Scanner"],
    summary="Analisar uma página web",
    responses={
        422: {"model": ErrorResponse, "description": "URL inválida"},
        503: {"model": ErrorResponse, "description": "Página inacessível"},
    },
)
async def scan_url(request: ScanRequest, http_request: Request, response: Response) -> ScanResponse:
    """
    Recebe uma URL e retorna um relatório de dark patterns detectados.

    **Sprint 7/11:** validação anti-SSRF por aplicação e filtro de requests.
    **Sprint 8:** scraping via Playwright/Chromium.
    **Sprint 9/10:** regras determinísticas integradas à interface.
    **Sprint 13:** etapa semântica opcional com fallback determinístico.
    **Microsprint 13.2:** verifica assimetria observável nas opções de consentimento.
    **Microsprint 13.3:** expõe apenas uma categoria segura quando o LLM falha.
    **Microsprint 15.1:** grava resumo anônimo no histórico local (SQLite).
    """
    started_at = time.monotonic()

    # ── 0. Controle de taxa (Microsprint 15.2) ────────────────
    _enforce_scan_rate_limit(http_request)

    # ── 1. Blindagem anti-SSRF ────────────────────────────────
    # DEVE ser a primeira verificação — antes de qualquer I/O de rede.
    try:
        check_ssrf(request.url)
    except SSRFError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "status": "error",
                "code": exc.code,
                "message": exc.message,
                "detail": None,
            },
        ) from exc

    # ── 2. Scraping real com Playwright (Sprint 8) ────────────
    try:
        page_data = await fetch_page(request.url)
    except ScraperError as exc:
        http_status = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if exc.code in ("PAGE_UNREACHABLE", "SCRAPER_INTERNAL")
            else status.HTTP_403_FORBIDDEN
        )
        raise HTTPException(
            status_code=http_status,
            detail={
                "status": "error",
                "code": exc.code,
                "message": exc.message,
                "detail": None,
            },
        ) from exc

    now_utc = datetime.now(timezone.utc).isoformat()
    domain  = urlparse(page_data.final_url).netloc.removeprefix("www.")

    # ── 3. Análise determinística de dark patterns (Sprint 9) ─
    raw_findings: list[ScanFinding] = analyze(
        html=page_data.html,
        text=page_data.text_content,
        visible_overlay_evidence=page_data.overlay_evidence,
        consent_choice_evidence=page_data.consent_choice_evidence,
        visible_countdown_evidence=page_data.countdown_evidence,
        visible_preselection_evidence=page_data.preselection_evidence,
        rendered_text_candidates=page_data.rendered_text_evidence,
        rendered_price_contexts=page_data.rendered_price_evidence,
    )

    # ── 4. Análise semântica opcional via LLM ─────────────────
    llm_result = await analyze_semantically(
        html=page_data.html,
        text=page_data.text_content,
    )
    existing = {
        (finding.id, " ".join(finding.evidence.strip(' \"\'…').split()).casefold())
        for finding in raw_findings
    }
    for finding in llm_result.findings:
        key = (finding.id, " ".join(finding.evidence.strip(' \"\'…').split()).casefold())
        if key not in existing:
            raw_findings.append(finding)
            existing.add(key)

    score = compute_score(raw_findings)
    llm_used = llm_result.status == "ok"

    # Mapeia ScanFinding → Finding (schema do contrato)
    dom_references = find_evidence_dom_references(page_data.html, raw_findings)
    findings = [
        Finding(
            id=f.id,
            type=f.type,
            severity=f.severity,
            evidence=f.evidence,
            dom_reference=dom_references[index],
            phase=f.phase,
            engine=f.engine,
        )
        for index, f in enumerate(raw_findings)
    ]

    duration_ms = round((time.monotonic() - started_at) * 1000)

    # ── 5. Histórico anônimo (modelo A — sem contas) ───────────
    # Guarda somente o recorte exibido no relatório: domínio, score,
    # achados curtos e metadados. URL completa e texto da página não
    # são persistidos. Falha de banco não derruba a análise.
    owner = _ensure_owner(http_request, response)
    report = {
        "scannedAt": now_utc,
        "domain": domain,
        "requestedDomain": (urlparse(request.url).hostname or "").removeprefix("www.") or None,
        "score": score,
        "riskLevel": _score_to_risk_level(score),
        "scanEngine": "hybrid" if llm_used else "deterministic",
        "llmStatus": llm_result.status,
        "llmUnavailableReason": llm_result.unavailable_reason,
        "durationMs": duration_ms,
        "domElementsScanned": page_data.dom_element_count,
        "rulesApplied": rules_count(),
        "visibleTextCharacters": len(page_data.text_content),
        "findings": [
            {
                "id": f.id,
                "type": f.type,
                "evidence": f.evidence[:240],
                "domReference": dom_references[i],
                "severity": f.severity,
                "engine": f.engine,
            }
            for i, f in enumerate(raw_findings[:10])
        ],
    }
    try:
        db.add_history_item(owner, report)
    except Exception:
        pass

    return ScanResponse(
        status="ok",
        url=request.url,
        domain=domain,
        scanned_at=now_utc,
        score=score,
        risk_level=_score_to_risk_level(score),
        findings=findings,
        meta=ScanMeta(
            phase=2 if llm_used else 1,
            engine="hybrid" if llm_used else "deterministic",
            llm_status=llm_result.status,
            llm_unavailable_reason=llm_result.unavailable_reason,
            duration_ms=duration_ms,
            rules_applied=rules_count(),
            dom_elements_scanned=page_data.dom_element_count,
            visible_text_characters=len(page_data.text_content),
        ),
    )


@app.get(
    "/api/history",
    tags=["Histórico"],
    summary="Listar resumos salvos deste navegador",
)
def get_history(request: Request, response: Response) -> dict:
    """Resumos anônimos vinculados ao cookie de identidade (mais novos primeiro)."""
    owner = _ensure_owner(request, response)
    try:
        items = db.list_history(owner)
    except Exception:
        items = []
    return {"items": items, "limit": db.HISTORY_LIMIT}


@app.delete(
    "/api/history",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Histórico"],
    summary="Apagar todo o histórico deste navegador",
)
def clear_history(request: Request, response: Response) -> None:
    owner = _ensure_owner(request, response)
    try:
        db.delete_history(owner)
    except Exception:
        pass


@app.delete(
    "/api/history/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Histórico"],
    summary="Remover um resumo do histórico",
)
def delete_history_item(item_id: str, request: Request, response: Response) -> None:
    owner = _ensure_owner(request, response)
    try:
        removed = db.delete_history_item(owner, item_id)
    except Exception:
        removed = False
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "code": "HISTORY_NOT_FOUND",
                "message": "Item não encontrado no histórico.",
                "detail": None,
            },
        )


# ── Frontend estático (Sprint 10) ─────────────────────────────
# Montado APÓS todas as rotas da API para não conflitar.
# Acesse: http://localhost:8000  (serve frontend/index.html)
import pathlib

_FRONTEND_DIR = pathlib.Path(__file__).parent.parent / "frontend"

if _FRONTEND_DIR.exists():
    from fastapi.staticfiles import StaticFiles as _StaticFiles
    # html=True → serve index.html automaticamente para "/"
    app.mount("/", _StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")


# ── Entrypoint direto (opcional) ──────────────────────────────
# Prefira rodar via: uvicorn backend.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=APP_PORT, reload=True)
