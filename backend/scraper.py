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
# Bounded window after DOMContentLoaded for client-side hydration and deferred copy.
# The scraper polls a compact DOM/text fingerprint and stops after a quiet window,
# subject to a minimum wait and this configurable cap. Avoid networkidle: many
# commerce sites keep requests open.
SCRAPER_RENDER_WAIT_MS: int = min(
    max(int(os.getenv("SCRAPER_RENDER_WAIT_MS", "3500")), 0), 5000
)
_RENDER_STABILITY_MIN_MS = 2000
_RENDER_STABILITY_QUIET_MS = 750
_RENDER_STABILITY_POLL_MS = 250
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
_OVERLAY_CANDIDATE_SELECTOR = (
    'dialog[open], [aria-modal="true"], [role="dialog"], '
    '[class*="modal"], [class*="popup"], [class*="overlay"], '
    '[class*="interstitial"], [class*="lightbox"], '
    '[class*="cookie"], [class*="consent"], [class*="gdpr"], '
    '[id*="modal"], [id*="popup"], [id*="cookie"], [id*="gdpr"]'
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
    overlay_evidence: list[str] = field(default_factory=list)
    consent_choice_evidence: list[dict[str, object]] = field(default_factory=list)
    countdown_evidence: list[str] = field(default_factory=list)
    preselection_evidence: list[str] = field(default_factory=list)
    rendered_text_evidence: list[str] = field(default_factory=list)
    rendered_price_evidence: list[dict[str, object]] = field(default_factory=list)


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

async def collect_visible_overlay_evidence(page: Page) -> list[str]:
    """Return text from visible elements that have strong overlay signals.

    A semantic role by itself is insufficient: accessible dialogs and skip links
    can exist in the DOM without behaving like a blocking overlay. Visibility,
    modal semantics, or overlay-like geometry/positioning must support the signal.
    """
    result = await page.evaluate(
        """(selector) => {
          const viewportArea = Math.max(1, window.innerWidth * window.innerHeight);
          const candidates = [...new Set(document.querySelectorAll(selector))].slice(0, 200);
          const isVisibleInViewport = (element) => {
            for (let node = element; node instanceof Element; node = node.parentElement) {
              const style = getComputedStyle(node);
              if (node.hasAttribute('hidden') ||
                  node.getAttribute('aria-hidden') === 'true' ||
                  style.display === 'none' ||
                  style.visibility === 'hidden' ||
                  style.visibility === 'collapse' ||
                  Number(style.opacity) <= 0.05) return false;
            }
            const rect = element.getBoundingClientRect();
            const width = Math.max(0, Math.min(rect.right, window.innerWidth) - Math.max(rect.left, 0));
            const height = Math.max(0, Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0));
            return width > 0 && height > 0;
          };

          const evidence = [];
          const seen = new Set();
          for (const element of candidates) {
            if (!isVisibleInViewport(element)) continue;
            const style = getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            const visibleWidth = Math.max(0, Math.min(rect.right, window.innerWidth) - Math.max(rect.left, 0));
            const visibleHeight = Math.max(0, Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0));
            const areaRatio = (visibleWidth * visibleHeight) / viewportArea;
            const zIndex = Number.parseInt(style.zIndex, 10);
            const elevated = Number.isFinite(zIndex) && zIndex >= 10;
            const fixed = style.position === 'fixed';
            const absolute = style.position === 'absolute';
            const name = `${element.id || ''} ${typeof element.className === 'string' ? element.className : ''}`;
            const text = (element.innerText || element.getAttribute('aria-label') || '')
              .replace(/\\s+/g, ' ').trim().slice(0, 160);
            if (/cookies?|consent|privacidade|privacy|lgpd|gdpr/i.test(`${name} ${text}`)) continue;
            const namedOverlay = /modal|popup|pop-up|overlay|interstitial|lightbox|cookie|consent|gdpr/i.test(name);
            const modalSemantics = element.matches('dialog[open], [aria-modal="true"]');
            const positionedOverlay = fixed && elevated && areaRatio >= 0.04;
            const namedPositionedOverlay = namedOverlay && (fixed || absolute) && (elevated || areaRatio >= 0.08);
            if (!modalSemantics && !positionedOverlay && !namedPositionedOverlay) continue;

            if (!text) continue;
            const key = text.toLocaleLowerCase();
            if (seen.has(key)) continue;
            seen.add(key);
            evidence.push(text);
            if (evidence.length >= 5) break;
          }
          return evidence;
        }""",
        _OVERLAY_CANDIDATE_SELECTOR,
    )
    return [item for item in result if isinstance(item, str) and item.strip()]


async def collect_visible_countdown_evidence(page: Page) -> list[str]:
    """Return visible, populated countdown-like text from named DOM elements."""
    result = await page.evaluate(
        """() => {
          const selector = [
            '[class*="countdown"]', '[class*="contagem"]',
            '[id*="countdown"]', '[id*="contagem"]', '[data-countdown]'
          ].join(',');
          const candidates = [...new Set(document.querySelectorAll(selector))].slice(0, 100);
          const timeValue = /\\b\\d{1,2}\\s*:\\s*\\d{2}(?:\\s*:\\s*\\d{2})?\\b|\\b\\d+\\s*(?:s|sec|secs|seconds?|seg|segundos?|min|mins|minutes?|minutos?|h|hrs?|hours?|horas?)\\b/i;
          const isVisible = (element) => {
            for (let node = element; node instanceof Element; node = node.parentElement) {
              const style = getComputedStyle(node);
              if (node.hasAttribute('hidden') || node.getAttribute('aria-hidden') === 'true' ||
                  style.display === 'none' || style.visibility === 'hidden' ||
                  style.visibility === 'collapse' || Number(style.opacity) <= 0.05) return false;
            }
            const rect = element.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.right > 0 &&
              rect.top < window.innerHeight && rect.left < window.innerWidth;
          };
          const evidence = [];
          const seen = new Set();
          for (const element of candidates) {
            if (!isVisible(element)) continue;
            const text = (element.innerText || element.getAttribute('aria-label') || '')
              .replace(/\\s+/g, ' ').trim().slice(0, 160);
            if (!text || !timeValue.test(text)) continue;
            const key = text.toLocaleLowerCase();
            if (seen.has(key)) continue;
            seen.add(key);
            evidence.push(text);
            if (evidence.length >= 3) break;
          }
          return evidence;
        }"""
    )
    return [item for item in result if isinstance(item, str) and item.strip()]


async def collect_visible_preselection_evidence(page: Page) -> list[str]:
    """Return labels for currently checked checkboxes that a user can see."""
    result = await page.evaluate(
        """() => {
          const checkboxes = [...document.querySelectorAll('input[type="checkbox"]')]
            .slice(0, 300);
          const isVisible = (element) => {
            for (let node = element; node instanceof Element; node = node.parentElement) {
              const style = getComputedStyle(node);
              if (node.hasAttribute('hidden') || node.getAttribute('aria-hidden') === 'true' ||
                  style.display === 'none' || style.visibility === 'hidden' ||
                  style.visibility === 'collapse' || Number(style.opacity) <= 0.05) return false;
            }
            const rect = element.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.right > 0 &&
              rect.top < window.innerHeight && rect.left < window.innerWidth;
          };
          const evidence = [];
          const seen = new Set();
          for (const checkbox of checkboxes) {
            if (!checkbox.checked || !checkbox.labels) continue;
            for (const label of checkbox.labels) {
              if (!isVisible(label)) continue;
              const text = (label.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 140);
              if (!text) continue;
              const key = text.toLocaleLowerCase();
              if (seen.has(key)) continue;
              seen.add(key);
              evidence.push(text);
              if (evidence.length >= 20) return evidence;
            }
          }
          return evidence;
        }"""
    )
    return [item for item in result if isinstance(item, str) and item.strip()]


async def collect_rendered_price_contexts(page: Page) -> list[dict[str, object]]:
    """Return old-price elements and their compact ancestor blocks, when rendered.

    The anchoring rule needs DOM context, not just loose text: for each visible
    old-price element we return its own text plus the enclosing ancestor texts
    (same 4-level, <=180-char walk the analyzer performs). Hidden elements and
    hidden ancestors are excluded.
    """
    result = await page.evaluate(
        """() => {
          const selector = [
            'del', 's',
            '[class*="price-old"]', '[class*="old-price"]',
            '[class*="price-before"]', '[class*="before-price"]',
            '[class*="price-original"]', '[class*="original-price"]',
            '[class*="was-price"]', '[class*="price-was"]',
            '[class*="compare-price"]', '[class*="regular-price"]',
            '[class*="preco-de"]', '[class*="de-por"]'
          ].join(',');
          const candidates = [...new Set(document.querySelectorAll(selector))].slice(0, 100);
          const isRendered = (element) => {
            for (let node = element; node instanceof Element; node = node.parentElement) {
              const style = getComputedStyle(node);
              if (node.hasAttribute('hidden') || node.getAttribute('aria-hidden') === 'true' ||
                  style.display === 'none' || style.visibility === 'hidden' ||
                  style.visibility === 'collapse' || Number(style.opacity) <= 0.05) return false;
            }
            const rect = element.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          };
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          const evidence = [];
          const seen = new Set();
          for (const element of candidates) {
            if (!isRendered(element)) continue;
            const old = clean(element.innerText).slice(0, 80);
            if (!old) continue;
            const contexts = [];
            let node = element;
            for (let i = 0; i < 4 && node instanceof Element; i += 1) {
              const ctx = clean(node.innerText);
              if (ctx.length > 180) break;
              contexts.push(ctx.slice(0, 200));
              node = node.parentElement;
            }
            if (!contexts.length) continue;
            const key = `${old}|${contexts.join('|')}`.toLocaleLowerCase();
            if (seen.has(key)) continue;
            seen.add(key);
            evidence.push({ old, contexts });
            if (evidence.length >= 10) break;
          }
          return evidence;
        }"""
    )
    return [item for item in result if isinstance(item, dict)]


async def collect_rendered_text_candidates(page: Page) -> list[str]:
    """Return short candidate texts from rendered elements, including below-fold content.

    Shared by text rules (scarcity, confirmshaming): only elements the browser
    actually rendered are eligible, so hidden markup cannot produce findings.
    """
    result = await page.evaluate(
        """() => {
          const candidates = [...document.querySelectorAll(
            'span, p, div, strong, b, em, small, li, button, a'
          )].slice(0, 500);
          const evidence = [];
          const seen = new Set();
          for (const element of candidates) {
            let hidden = false;
            for (let node = element; node instanceof Element; node = node.parentElement) {
              const style = getComputedStyle(node);
              if (node.hasAttribute('hidden') || node.getAttribute('aria-hidden') === 'true' ||
                  style.display === 'none' || style.visibility === 'hidden' ||
                  style.visibility === 'collapse' || style.contentVisibility === 'hidden' ||
                  Number(style.opacity) <= 0.05) {
                hidden = true;
                break;
              }
            }
            if (hidden) continue;
            const text = (element.innerText || '').replace(/\\s+/g, ' ').trim();
            if (!text || text.length > 200) continue;
            const rect = element.getBoundingClientRect();
            if (!(rect.width > 0 && rect.height > 0) && element.getClientRects().length === 0) continue;
            const key = text.toLocaleLowerCase();
            if (seen.has(key)) continue;
            seen.add(key);
            evidence.push(text);
            if (evidence.length >= 500) break;
          }
          return evidence;
        }"""
    )
    return [item for item in result if isinstance(item, str) and item.strip()]


async def collect_visible_consent_choices(page: Page) -> list[dict[str, object]]:
    """Extract visible consent controls and their relative visual emphasis."""
    result = await page.evaluate(
        """(selector) => {
          const viewportArea = Math.max(1, window.innerWidth * window.innerHeight);
          const candidates = [...new Set(document.querySelectorAll(selector))].slice(0, 200);
          const isVisibleInViewport = (element) => {
            for (let node = element; node instanceof Element; node = node.parentElement) {
              const style = getComputedStyle(node);
              if (node.hasAttribute('hidden') ||
                  node.getAttribute('aria-hidden') === 'true' ||
                  style.display === 'none' || style.visibility === 'hidden' ||
                  style.visibility === 'collapse' || Number(style.opacity) <= 0.05) return false;
            }
            const rect = element.getBoundingClientRect();
            return rect.right > 0 && rect.bottom > 0 &&
              rect.left < window.innerWidth && rect.top < window.innerHeight &&
              rect.width > 0 && rect.height > 0;
          };
          const evidence = [];
          const seen = new Set();
          const consentWords = /cookies?|consent|privacidade|privacy|lgpd|gdpr/i;
          const controlSelector = 'button, a[href], [role="button"], input[type="button"], input[type="submit"]';

          for (const container of candidates) {
            if (!isVisibleInViewport(container)) continue;
            const containerText = (container.innerText || '').replace(/\\s+/g, ' ').trim();
            const identity = `${container.id || ''} ${typeof container.className === 'string' ? container.className : ''}`;
            if (!consentWords.test(`${identity} ${containerText.slice(0, 1000)}`)) continue;

            const style = getComputedStyle(container);
            const rect = container.getBoundingClientRect();
            const areaRatio = (Math.max(0, Math.min(rect.right, window.innerWidth) - Math.max(rect.left, 0)) *
              Math.max(0, Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0))) / viewportArea;
            const zIndex = Number.parseInt(style.zIndex, 10);
            const elevated = Number.isFinite(zIndex) && zIndex >= 10;
            const fixed = style.position === 'fixed';
            const absolute = style.position === 'absolute';
            const modalSemantics = container.matches('dialog[open], [aria-modal="true"]');
            const namedConsent = consentWords.test(identity);
            const positionedOverlay = fixed && elevated && areaRatio >= 0.04;
            const namedPositionedOverlay = namedConsent && (fixed || absolute) && (elevated || areaRatio >= 0.08);
            if (!modalSemantics && !positionedOverlay && !namedPositionedOverlay) continue;

            const controls = [...container.querySelectorAll(controlSelector)];
            if (container.matches(controlSelector)) controls.unshift(container);
            const actions = [];
            for (const control of controls) {
              if (!isVisibleInViewport(control) || control.disabled ||
                  control.getAttribute('aria-disabled') === 'true') continue;
              const label = (control.innerText || control.getAttribute('aria-label') ||
                control.getAttribute('title') || control.value || '')
                .replace(/\\s+/g, ' ').trim().slice(0, 100);
              if (!label) continue;

              const controlStyle = getComputedStyle(control);
              const color = controlStyle.backgroundColor;
              const colorParts = (color.match(/rgba?\\(([^)]+)\\)/i)?.[1] || '')
                .split(/[,/ ]+/).filter(Boolean);
              const alpha = color === 'transparent' ? 0 :
                colorParts.length >= 4 ? Number(colorParts[3]) : 1;
              const hasBorder = ['Top', 'Right', 'Bottom', 'Left'].some((side) =>
                parseFloat(controlStyle[`border${side}Width`]) > 0 &&
                controlStyle[`border${side}Style`] !== 'none');
              const weight = Number.parseInt(controlStyle.fontWeight, 10) || 400;
              const buttonLike = control.tagName === 'BUTTON' ||
                control.getAttribute('role') === 'button' ||
                control.matches('input[type="button"], input[type="submit"]');
              const bounds = control.getBoundingClientRect();
              const area = bounds.width * bounds.height;
              const prominence = (alpha >= 0.75 ? 2 : alpha >= 0.25 ? 1 : 0) +
                (hasBorder ? 1 : 0) + (weight >= 600 ? 1 : 0) + (buttonLike ? 0.5 : 0);
              actions.push({
                label,
                control: control.tagName.toLowerCase(),
                prominence,
                area,
              });
              if (actions.length >= 12) break;
            }

            if (!actions.length) continue;
            const key = actions.map((action) => action.label.toLocaleLowerCase()).sort().join('|');
            if (seen.has(key)) continue;
            seen.add(key);
            evidence.push({
              container_text: containerText.slice(0, 240),
              actions,
            });
            if (evidence.length >= 3) break;
          }
          return evidence;
        }""",
        _OVERLAY_CANDIDATE_SELECTOR,
    )
    return [item for item in result if isinstance(item, dict)]


async def _wait_for_render_stability(page: Page, max_wait_ms: int) -> None:
    """Wait briefly for text/DOM changes to settle, without waiting for network idle."""
    if max_wait_ms <= 0:
        return

    started = time.monotonic()
    minimum_wait_ms = min(_RENDER_STABILITY_MIN_MS, max_wait_ms)
    deadline = started + (max_wait_ms / 1000)
    previous_signature: str | None = None
    quiet_since: float | None = None

    while True:
        now = time.monotonic()
        remaining = deadline - now
        if remaining <= 0:
            return

        try:
            signature = await asyncio.wait_for(
                page.evaluate(
                    """() => {
                      const text = document.body?.innerText ?? '';
                      const sample = text.slice(0, 50000);
                      let hash = 2166136261;
                      for (let i = 0; i < sample.length; i += 1) {
                        hash = Math.imul(hash ^ sample.charCodeAt(i), 16777619);
                      }
                      return `${text.length}:${document.querySelectorAll('*').length}:${hash >>> 0}`;
                    }"""
                ),
                timeout=remaining,
            )
        except asyncio.TimeoutError:
            return
        except PlaywrightError:
            # A client-side navigation may replace the execution context mid-poll.
            previous_signature = None
            quiet_since = None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            await asyncio.sleep(min(_RENDER_STABILITY_POLL_MS / 1000, remaining))
            continue

        now = time.monotonic()
        if now >= deadline:
            return
        elapsed_ms = (now - started) * 1000
        if elapsed_ms >= minimum_wait_ms:
            if signature != previous_signature:
                quiet_since = now
            elif quiet_since is None:
                quiet_since = now

            if (
                quiet_since is not None
                and (now - quiet_since) * 1000 >= _RENDER_STABILITY_QUIET_MS
            ):
                return
        else:
            quiet_since = None

        previous_signature = signature
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        await asyncio.sleep(min(_RENDER_STABILITY_POLL_MS / 1000, remaining))


def _validate_final_destination(final_url: str, requested_url: str) -> None:
    """Revalidate navigated URLs so redirects cannot reach private addresses."""
    if final_url == requested_url:
        return
    try:
        check_ssrf(final_url)
    except SSRFError:
        raise ScraperError(
            "PAGE_UNREACHABLE",
            "A página redirecionou para um endereço interno (DNS rebinding bloqueado).",
        )


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
    _validate_final_destination(final_url, url)

    # Give client-side applications a bounded window to hydrate and render text.
    await _wait_for_render_stability(page, SCRAPER_RENDER_WAIT_MS)

    # Client-side redirects can occur during the render window; validate again.
    updated_final_url = page.url
    if updated_final_url != final_url:
        _validate_final_destination(updated_final_url, url)
        final_url = updated_final_url

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
        overlay_evidence = await collect_visible_overlay_evidence(page)
        consent_choice_evidence = await collect_visible_consent_choices(page)
        countdown_evidence = await collect_visible_countdown_evidence(page)
        preselection_evidence = await collect_visible_preselection_evidence(page)
        rendered_text_evidence = await collect_rendered_text_candidates(page)
        rendered_price_evidence = await collect_rendered_price_contexts(page)
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
        overlay_evidence=overlay_evidence,
        consent_choice_evidence=consent_choice_evidence,
        countdown_evidence=countdown_evidence,
        preselection_evidence=preselection_evidence,
        rendered_text_evidence=rendered_text_evidence,
        rendered_price_evidence=rendered_price_evidence,
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
