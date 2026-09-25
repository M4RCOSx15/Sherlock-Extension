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
import os
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

from playwright.async_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

from backend.security import SSRFError, check_ssrf

# ── Configuração ──────────────────────────────────────────────
SCRAPER_TIMEOUT_MS: int = int(os.getenv("SCRAPER_TIMEOUT_MS", "15000"))
SCRAPER_USER_AGENT = (
    "RASTRO-Scanner/0.1 (audit bot; +https://rastro.dev/bot)"
)


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
    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
            ],
        )
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
        # Bloqueia permissões sensíveis
        permissions=[],
    )

    # Bloqueia recursos desnecessários para economizar banda/tempo
    await context.route(
        "**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2,ttf,eot,mp4,mp3,wav}",
        lambda route, _req: route.abort(),
    )

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

    duration_ms = int((time.monotonic() - t_start) * 1000)

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
