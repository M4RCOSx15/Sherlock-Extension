"""
RASTRO — Scraper com Playwright (Sprint 8)

Extrai HTML, título e metadados básicos de uma URL pública usando
Chromium headless. A análise de dark patterns será adicionada na Sprint 9.

Uso:
    from backend.scraper import fetch_page, ScraperError, PageData

    try:
        page = await fetch_page("https://exemplo.com")
        print(page.title, len(page.html))
    except ScraperError as e:
        # código: PAGE_UNREACHABLE | ACCESS_BLOCKED | SCRAPER_INTERNAL
        ...

SEGURANÇA:
    - A blindagem anti-SSRF (backend/security.py) deve ser chamada ANTES
      desta função. O main.py garante essa ordem.
    - O Playwright roda sem permissões de geolocalização/câmera/notificações.
    - User-agent identifica o scanner (não faz spoofing de navegador real).
    - Tempo máximo de scraping: SCRAPER_TIMEOUT_MS (env: SCRAPER_TIMEOUT_MS).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

from playwright.async_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    Request,
    Route,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

from backend.security import SSRFError, check_ssrf

LOGGER = logging.getLogger(__name__)

# ── Configuração ──────────────────────────────────────────────
SCRAPER_TIMEOUT_MS: int = int(os.getenv("SCRAPER_TIMEOUT_MS", "15000"))
# Small, bounded pause after DOMContentLoaded for client-side hydration and deferred copy.
# Avoid networkidle: many commerce sites keep requests open.
SCRAPER_RENDER_WAIT_MS: int = min(
    max(int(os.getenv("SCRAPER_RENDER_WAIT_MS", "1800")), 0), 5000
)
SCRAPER_PROXY_URL = os.getenv("SCRAPER_PROXY_URL", "").strip()
SCRAPER_PROXY_REQUIRED = (
    os.getenv("APP_ENV", "development").lower() == "production"
    or os.getenv("SCRAPER_PROXY_REQUIRED", "false").lower()
    in {"1", "true", "yes"}
)
SCRAPER_USER_AGENT = (
    "RASTRO-Scanner/0.1 (audit bot; +https://rastro.dev/bot)"
)
_BLOCKED_RESOURCE_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".wav",
})


# ── Tipos de dados ────────────────────────────────────────────

@dataclass
class PageData:
    """Resultado de um scraping bem-sucedido."""
    url: str                    # URL original solicitada
    final_url: str              # URL após redirects
    title: str                  # <title> da página
    html: str                   # HTML completo (document.documentElement.outerHTML)
    text_content: str           # Texto visível (body.innerText)
    status_code: int            # HTTP status da navegação principal
    duration_ms: int            # Tempo total de scraping em ms
    dom_element_count: int = 0  # Número de elementos no DOM


class ScraperError(RuntimeError):
    """
    Levantada quando o scraping falha.

    Attributes:
        code: "PAGE_UNREACHABLE" | "ACCESS_BLOCKED" | "SCRAPER_INTERNAL"
        message: Mensagem segura para exibir ao usuário.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ── API pública ───────────────────────────────────────────────

async def fetch_page(
    url: str,
    timeout_ms: int = SCRAPER_TIMEOUT_MS,
) -> PageData:
    """
    Abre a URL com Playwright/Chromium headless e retorna os dados da página.

    Args:
        url: URL pública já validada pelo guard anti-SSRF.
        timeout_ms: Timeout máximo de navegação em milissegundos.

    Returns:
        PageData com HTML, título, texto e metadados.

    Raises:
        ScraperError: Em caso de timeout, bloqueio anti-bot ou erro interno.
    """
    if SCRAPER_PROXY_REQUIRED and not SCRAPER_PROXY_URL:
        raise ScraperError(
            "SCRAPER_INTERNAL",
            "A análise foi interrompida: o proxy de saída obrigatório não está configurado.",
        )

    async with async_playwright() as pw:
        launch_options: dict[str, object] = {
            "headless": True,
            "chromium_sandbox": True,
            "args": [
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
            ],
        }
        if SCRAPER_PROXY_URL:
            launch_options["proxy"] = {
                "server": SCRAPER_PROXY_URL,
                # Chromium otherwise bypasses configured proxies for loopback.
                # That would bypass the egress proxy's local-address checks.
                "bypass": "<-loopback>",
            }

        try:
            browser: Browser = await pw.chromium.launch(**launch_options)
        except PlaywrightError as exc:
            # Keep the public API response generic, but preserve the actual
            # browser launch failure in backend logs for container diagnosis.
            LOGGER.exception("Chromium launch failed with sandbox/proxy policy")
            raise ScraperError(
                "SCRAPER_INTERNAL",
                "Não foi possível iniciar o navegador com a política de rede configurada.",
            ) from exc
        try:
            return await _scrape(browser, url, timeout_ms)
        finally:
            await browser.close()


# ── Implementação interna ─────────────────────────────────────

async def _scrape(browser: Browser, url: str, timeout_ms: int) -> PageData:
    context: BrowserContext = await browser.new_context(
        user_agent=SCRAPER_USER_AGENT,
        java_script_enabled=True,
        bypass_csp=False,
        service_workers="block",
        # Bloqueia permissões sensíveis
        permissions=[],
    )

    # Defesa em profundidade: valida cada URL HTTP(S) que o navegador tenta
    # carregar (documento, iframe, script, fetch, stylesheet etc.) antes de
    # permitir a requisição. Service workers ficam bloqueados para que não
    # contornem a interceptação.
    await context.route("**/*", _guard_browser_request)

    page: Page = await context.new_page()
    t_start = time.monotonic()

    try:
        response = await page.goto(
            url,
            timeout=timeout_ms,
            wait_until="domcontentloaded",
        )
    except PlaywrightTimeout:
        raise ScraperError(
            "PAGE_UNREACHABLE",
            f"A página não respondeu dentro de {timeout_ms // 1000} s. "
            "Verifique se o endereço está correto e acessível publicamente.",
        )
    except PlaywrightError as exc:
        msg = str(exc).lower()
        if "net::err_" in msg or "navigation" in msg:
            raise ScraperError(
                "PAGE_UNREACHABLE",
                "Não foi possível estabelecer conexão com a página.",
            )
        raise ScraperError("SCRAPER_INTERNAL", f"Erro inesperado do scraper: {exc}")

    # Verifica status HTTP
    if response is None:
        raise ScraperError("PAGE_UNREACHABLE", "Sem resposta do servidor.")

    status = response.status
    if status == 403 or status == 429:
        raise ScraperError(
            "ACCESS_BLOCKED",
            f"A página bloqueou o acesso automatizado (HTTP {status}). "
            "O RASTRO não tenta bypassar proteções anti-bot.",
        )
    if status >= 400:
        raise ScraperError(
            "PAGE_UNREACHABLE",
            f"O servidor retornou HTTP {status}.",
        )

    final_url: str = page.url

    # ── Mitigação de DNS rebinding: revalida a URL final ──────
    # Se a página redirecionou para um endereço interno, bloqueamos.
    if final_url != url:
        try:
            check_ssrf(final_url)
        except SSRFError:
            raise ScraperError(
                "PAGE_UNREACHABLE",
                "A página redirecionou para um endereço interno (DNS rebinding bloqueado).",
            )

    # Give client-side applications a short, bounded window to hydrate and render deferred text.
    # This deliberately does not wait for networkidle, which can hang on commerce sites.
    if SCRAPER_RENDER_WAIT_MS:
        await page.wait_for_timeout(SCRAPER_RENDER_WAIT_MS)

    # Extrai dados do DOM
    try:
        html: str = await page.content()
        title: str = await page.title()
        text_content: str = await page.evaluate(
            "() => document.body?.innerText?.trim() ?? ''"
        )
        dom_count: int = await page.evaluate(
            "() => document.querySelectorAll('*').length"
        )
        duration_ms = int((time.monotonic() - t_start) * 1000)
    except PlaywrightError as exc:
        raise ScraperError("SCRAPER_INTERNAL", f"Erro ao extrair dados da página: {exc}")

    return PageData(
        url=url,
        final_url=final_url,
        title=title,
        html=html,
        text_content=text_content,
        status_code=status,
        duration_ms=duration_ms,
        dom_element_count=dom_count,
    )


async def _guard_browser_request(route: Route, request: Request) -> None:
    """Aplica filtro de destino e corta recursos pesados antes da rede.

    Este filtro reduz tráfego para destinos internos, mas não substitui
    isolamento de rede: redirects e DNS rebinding ainda precisam de uma
    barreira de egress no ambiente que executa o Chromium.
    """
    parsed = urlparse(request.url)
    if parsed.scheme.lower() not in {"http", "https"}:
        await route.abort("blockedbyclient")
        return

    if (parsed.path.rsplit("/", 1)[-1].lower().endswith(
        tuple(_BLOCKED_RESOURCE_SUFFIXES)
    )):
        await route.abort()
        return

    try:
        # getaddrinfo é síncrono; mantê-lo fora do event loop evita travar a
        # API enquanto valida requests secundários da página.
        await asyncio.to_thread(check_ssrf, request.url)
    except (SSRFError, ValueError, OSError):
        await route.abort("blockedbyclient")
        return

    await route.continue_()
