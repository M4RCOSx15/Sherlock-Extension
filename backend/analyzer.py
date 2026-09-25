"""
RASTRO — Motor determinístico de detecção de dark patterns (Sprint 9)

Analisa o HTML + texto de uma página e retorna findings tipados.
Cada regra usa regex e/ou seletores CSS via BeautifulSoup.

Uso:
    from backend.analyzer import analyze, ScanFinding

    findings = analyze(html=page_data.html, text=page_data.text_content)
    score    = compute_score(findings)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from bs4 import BeautifulSoup, Tag


# ── Tipos ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class ScanFinding:
    """Finding produzido pelo motor determinístico."""
    id: str
    type: str
    severity: str      # "low" | "medium" | "high" | "critical"
    evidence: str
    phase: int = 1
    engine: str = "deterministic"


# ── Pesos de severidade (para cálculo de score) ───────────────
SEVERITY_WEIGHT: dict[str, int] = {
    "critical": 30,
    "high":     20,
    "medium":   10,
    "low":       5,
}


# ── Helpers ───────────────────────────────────────────────────

def _first_match(pattern: re.Pattern[str], text: str, max_len: int = 120) -> str | None:
    """Retorna a primeira correspondência do regex, truncada a max_len chars."""
    m = pattern.search(text)
    if m:
        snippet = m.group(0).strip()
        return snippet[:max_len] + ("…" if len(snippet) > max_len else "")
    return None


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _visible_text(tag: Tag) -> str:
    """Extrai o texto visível de uma tag, colapsando espaços."""
    return " ".join(tag.get_text(" ", strip=True).split())


# ── Definição de regras ───────────────────────────────────────
# Cada regra é uma callable: (html, text_content) -> list[ScanFinding]

RuleFn = Callable[[str, str], list[ScanFinding]]

_RULES: list[RuleFn] = []


def _rule(fn: RuleFn) -> RuleFn:
    _RULES.append(fn)
    return fn


# ─── Regra 1: Falsa Escassez ──────────────────────────────────
_SCARCITY_RE = re.compile(
    r"""(
        (?:s[oó](?:mente)?|apenas|somente|restam?|left|only|last|[úu]ltim[ao]s?)\s*
        \d+\s*
        (?:unidade?s?|item?s?|pe[çc]a?s?|em?\s*estoque|in\s+stock|vagas?|spots?)
      |
        (?:estoque\s+)?(?:limitad[ao]|esgotand[oa])
      |
        \b(?:hurry|corra|apresse[-\s]?se|acabando)\b
    )""",
    re.IGNORECASE | re.VERBOSE,
)


@_rule
def _check_fake_scarcity(html: str, text: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    soup = _soup(html)

    # Texto visível de badges, botões, spans, parágrafos
    candidates = soup.find_all(
        ["span", "p", "div", "strong", "b", "em", "small", "li", "button"],
        limit=500,
    )
    seen: set[str] = set()
    for tag in candidates:
        t = _visible_text(tag)
        if len(t) > 200 or not t:
            continue
        evidence = _first_match(_SCARCITY_RE, t)
        if evidence and evidence not in seen:
            seen.add(evidence)
            findings.append(ScanFinding(
                id="fake_scarcity",
                type="Falsa escassez",
                severity="high",
                evidence=f'"{evidence}"',
            ))
            if len(findings) >= 3:
                break
    return findings


# ─── Regra 2: Urgência Fabricada ─────────────────────────────
_URGENCY_RE = re.compile(
    r"""(
        (?:oferta?|promo[çc][aã]o|desconto|sale|deal)\s*
        (?:termina?|expira?|acaba?|ends?)\s*
        (?:em|in|at|hoje|today|agora|now)?
      |
        (?:hoje\s+(?:apenas?|somente|s[oó])|only\s+today)
      |
        (?:últimas?\s+(?:horas?|minutos?|dias?)
          |last\s+(?:hours?|minutes?|days?))
      |
        (?:contador|countdown|timer|contagem\s+regressiva)
    )""",
    re.IGNORECASE | re.VERBOSE,
)

# Seletores CSS comuns de countdown
_COUNTDOWN_SELECTORS = [
    "[class*=countdown]", "[class*=timer]", "[class*=contagem]",
    "[id*=countdown]",    "[id*=timer]",    "[data-countdown]",
    "[data-timer]",
]


@_rule
def _check_fake_urgency(html: str, text: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    soup = _soup(html)

    # 1. Detecta countdown via CSS selectors
    for sel in _COUNTDOWN_SELECTORS:
        try:
            el = soup.select_one(sel)
        except Exception:
            continue
        if el:
            snippet = _visible_text(el)[:80] or f"<{el.name}>"
            findings.append(ScanFinding(
                id="fake_urgency",
                type="Urgência fabricada",
                severity="high",
                evidence=f"Contador regressivo detectado: \"{snippet}\"",
            ))
            break

    # 2. Detecta padrões de texto
    if not findings:
        evidence = _first_match(_URGENCY_RE, text)
        if evidence:
            findings.append(ScanFinding(
                id="fake_urgency",
                type="Urgência fabricada",
                severity="medium",
                evidence=f'"{evidence}"',
            ))
    return findings


# ─── Regra 3: Confirmshaming ──────────────────────────────────
_CONFIRMSHAMING_RE = re.compile(
    r"""(
        n[aã]o[,\s]+(?:obrigad[oa]|quero|prefiro|preciso|desejo|gostaria)
      | (?:prefiro|quero)\s+(?:ficar\s+sem|perder|pagar\s+mais)
      | (?:no[,\s]+thanks?|no[,\s]+thank\s+you)
      | (?:skip|ignore|dismiss)\s+(?:this|deal|offer|opportunity)
      | i\s+(?:don.t|do\s+not)\s+want\s+(?:to\s+save|discounts?|deals?)
    )""",
    re.IGNORECASE | re.VERBOSE,
)


@_rule
def _check_confirmshaming(html: str, text: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    soup = _soup(html)

    # Foca em links e botões de recusa
    candidates = soup.find_all(
        ["a", "button", "span", "p"],
        limit=300,
    )
    seen: set[str] = set()
    for tag in candidates:
        t = _visible_text(tag)
        if len(t) > 100 or not t:
            continue
        evidence = _first_match(_CONFIRMSHAMING_RE, t)
        if evidence and evidence not in seen:
            seen.add(evidence)
            findings.append(ScanFinding(
                id="confirmshaming",
                type="Indução à culpa (confirmshaming)",
                severity="medium",
                evidence=f'"{evidence}"',
            ))
            if len(findings) >= 2:
                break
    return findings


# ─── Regra 4: Ancoragem de Preço ─────────────────────────────
_PRICE_SELECTORS = [
    "del", "s",
    "[class*=price-old]",    "[class*=old-price]",
    "[class*=price-before]", "[class*=before-price]",
    "[class*=price-original]","[class*=original-price]",
    "[class*=was-price]",    "[class*=price-was]",
    "[class*=compare-price]","[class*=regular-price]",
    "[class*=preco-de]",     "[class*=de-por]",
]

_PRICE_RE = re.compile(r"(?:R\$|USD|\$|€|£)\s*[\d.,]+")


@_rule
def _check_price_anchoring(html: str, text: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    soup = _soup(html)

    for sel in _PRICE_SELECTORS:
        try:
            els = soup.select(sel, limit=5)
        except Exception:
            continue
        for el in els:
            t = _visible_text(el)
            if _PRICE_RE.search(t):
                findings.append(ScanFinding(
                    id="price_anchoring",
                    type="Ancoragem de preço",
                    severity="medium",
                    evidence=f'Preço riscado detectado: "{t[:60]}"',
                ))
                break  # um finding por selector é suficiente
        if findings:
            break
    return findings[:1]  # no máximo 1 finding desta regra


# ─── Regra 5: Pré-seleção Oculta ─────────────────────────────
_OPTIN_WORDS = re.compile(
    r"(newsletter|email\s+market|promo[çc][aõ]|mailing|parceiro|oferta|publicidade)",
    re.IGNORECASE,
)


@_rule
def _check_hidden_preselection(html: str, text: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    soup = _soup(html)

    checkboxes = soup.find_all("input", {"type": "checkbox"})
    for cb in checkboxes:
        # Checado por padrão
        if cb.get("checked") is None:
            continue
        # Busca label associado
        label_text = ""
        label_id = cb.get("id")
        if label_id:
            label_tag = soup.find("label", {"for": label_id})
            if label_tag:
                label_text = _visible_text(label_tag)
        if not label_text:
            # Tenta label pai
            parent = cb.find_parent("label")
            if parent:
                label_text = _visible_text(parent)

        # Só sinaliza se o label mencionar marketing/newsletter
        if _OPTIN_WORDS.search(label_text):
            findings.append(ScanFinding(
                id="hidden_preselection",
                type="Pré-seleção oculta",
                severity="high",
                evidence=f'Checkbox de marketing pré-selecionado: "{label_text[:100]}"',
            ))
        elif cb.get("checked") is not None and not label_text:
            # Checkbox marcado sem label visível — suspeito
            name = cb.get("name", "?")
            findings.append(ScanFinding(
                id="hidden_preselection",
                type="Pré-seleção oculta",
                severity="medium",
                evidence=f'Checkbox pré-selecionado sem label visível (name="{name}")',
            ))

    return findings[:2]


# ─── Regra 6: Dark Overlay / Pop-up Intrusivo ────────────────
_OVERLAY_SELECTORS = [
    "[role=dialog]",       "[aria-modal=true]",
    "[class*=modal]",      "[class*=popup]",
    "[class*=overlay]",    "[class*=popover]",
    "[class*=interstitial]","[class*=lightbox]",
    "[id*=modal]",         "[id*=popup]",
    "[id*=cookie]",        "[class*=cookie]",
    "[class*=gdpr]",       "[id*=gdpr]",
]


@_rule
def _check_dark_overlay(html: str, text: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    soup = _soup(html)

    for sel in _OVERLAY_SELECTORS:
        try:
            el = soup.select_one(sel)
        except Exception:
            continue
        if el:
            snippet = _visible_text(el)[:80] or sel
            findings.append(ScanFinding(
                id="dark_overlay",
                type="Pop-up / overlay intrusivo",
                severity="medium",
                evidence=f'Elemento sobrepositor detectado: "{snippet}"',
            ))
            break

    return findings


# ── API pública ───────────────────────────────────────────────

def analyze(html: str, text: str) -> list[ScanFinding]:
    """
    Executa todas as regras determinísticas sobre o HTML e texto da página.

    Args:
        html: HTML completo da página (document.documentElement.outerHTML).
        text: Texto visível da página (body.innerText).

    Returns:
        Lista de ScanFinding. Pode ser vazia se nenhum padrão for detectado.
    """
    all_findings: list[ScanFinding] = []
    for rule_fn in _RULES:
        try:
            all_findings.extend(rule_fn(html, text))
        except Exception:
            # Regra com bug não deve derrubar a análise inteira.
            pass
    return all_findings


def compute_score(findings: list[ScanFinding]) -> int:
    """
    Calcula o score de risco agregado (0–100).
    Fórmula: min(100, soma dos pesos por severidade).
    """
    total = sum(SEVERITY_WEIGHT.get(f.severity, 0) for f in findings)
    return min(100, total)


def rules_count() -> int:
    """Retorna o número de regras registradas."""
    return len(_RULES)
