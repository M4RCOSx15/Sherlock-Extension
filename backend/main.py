"""
RASTRO — Backend API
Sprint 7: blindagem anti-SSRF integrada ao endpoint de scan.
O scraping real será adicionado na Sprint 8 (Playwright).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from backend.security import SSRFError, check_ssrf

# ── Configuração ─────────────────────────────────────────────
load_dotenv()

APP_VERSION = "0.1.0"
APP_ENV     = os.getenv("APP_ENV", "development")
APP_PORT    = int(os.getenv("APP_PORT", "8000"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

# ── Aplicação ─────────────────────────────────────────────────
app = FastAPI(
    title="RASTRO API",
    description=(
        "Scanner de dark patterns e copywriting manipulativo em páginas web.\n\n"
        "> **Sprint 6 — Stub:** o endpoint `/api/scan` retorna dados fictícios. "
        "O scraping real entra na Sprint 8."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
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
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
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
    phase: int          # 1 = determinístico | 2 = LLM
    engine: str         # "deterministic" | "llm" | "stub"


class ScanMeta(BaseModel):
    phase: int
    engine: str
    duration_ms: int
    rules_applied: int
    dom_elements_scanned: int


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
def scan_url(request: ScanRequest) -> ScanResponse:
    """
    Recebe uma URL e retorna um relatório de dark patterns detectados.

    **Sprint 7:** validação anti-SSRF ativa — URLs internas são rejeitadas com 422.
    **Sprint 6 — STUB:** retorna dados fictícios enquanto o Playwright não está integrado.
    """
    # ── Blindagem anti-SSRF (Sprint 7) ────────────────────────
    # Deve ser a PRIMEIRA verificação — antes de qualquer I/O de rede.
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
    parsed  = urlparse(request.url)
    domain  = parsed.netloc.removeprefix("www.")
    now_utc = datetime.now(timezone.utc).isoformat()

    # ── TODO (Sprint 8): substituir por scraping real via Playwright ──
    stub_findings: list[Finding] = [
        Finding(
            id="stub_finding",
            type="[STUB] Dado fictício",
            severity="low",
            evidence="Scraping não implementado ainda (Sprint 8). "
                     f"URL recebida: {request.url}",
            phase=1,
            engine="stub",
        )
    ]
    stub_score = 0

    return ScanResponse(
        status="ok",
        url=request.url,
        domain=domain,
        scanned_at=now_utc,
        score=stub_score,
        risk_level=_score_to_risk_level(stub_score),
        findings=stub_findings,
        meta=ScanMeta(
            phase=1,
            engine="stub",
            duration_ms=0,
            rules_applied=0,
            dom_elements_scanned=0,
        ),
    )


# ── Entrypoint direto (opcional) ──────────────────────────────
# Prefira rodar via: uvicorn backend.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=APP_PORT, reload=True)
