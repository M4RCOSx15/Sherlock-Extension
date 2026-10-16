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
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
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


_QUOTED_EVIDENCE_RE = re.compile(r'["“]([^"”]{3,180})["”]')


def _normalise_dom_text(value: str) -> str:
    return " ".join(value.split()).casefold()


def _positional_dom_path(tag: Tag) -> str:
    """Build a selector using tag names and sibling positions only.

    Avoid IDs, classes, attributes, and page text: those values can contain
    personal data or arbitrary content supplied by the scanned site.
    """
    parts: list[str] = []
    current: Tag | None = tag
    while isinstance(current, Tag) and current.name != "[document]":
        position = 1
        for sibling in current.previous_siblings:
            if isinstance(sibling, Tag) and sibling.name == current.name:
                position += 1
        if not re.fullmatch(r"[a-z][a-z0-9-]*", current.name or ""):
            return ""
        parts.append(f"{current.name}:nth-of-type({position})")
        current = current.parent if isinstance(current.parent, Tag) else None
    parts.reverse()
    path = " > ".join(parts)
    return path if len(path) <= 500 else ""


def find_evidence_dom_references(html: str, findings: list[ScanFinding]) -> list[str | None]:
    """Map quoted finding excerpts to positional paths in the captured DOM.

    The reference is structural and snapshot-specific. It is omitted when a
    quoted excerpt cannot be located safely in the captured markup.
    """
    targets: list[str | None] = []
    for finding in findings:
        match = _QUOTED_EVIDENCE_RE.search(finding.evidence)
        excerpt = match.group(1).strip() if match else ""
        excerpt = re.sub(r"(?:…|\.\.\.)$", "", excerpt).strip()
        targets.append(_normalise_dom_text(excerpt) if len(excerpt) >= 3 else None)

    all_targets = {target for target in targets if target}
    if not all_targets:
        return [None] * len(findings)

    soup = _soup(html)
    located: dict[str, tuple[int, int, str]] = {}

    def consider(target: str, tag: Tag, text_length: int) -> None:
        path = _positional_dom_path(tag)
        if not path:
            return
        depth = path.count(" > ")
        previous = located.get(target)
        if previous is None or (text_length, -depth) < (previous[0], -previous[1]):
            located[target] = (text_length, depth, path)

    # First prefer a single text node, which usually identifies the smallest
    # useful element even when its ancestors repeat the same text.
    for text_node in soup.find_all(string=True, limit=30000):
        parent = text_node.parent
        if not isinstance(parent, Tag) or parent.name in {"script", "style", "noscript", "template"}:
            continue
        text_value = _normalise_dom_text(str(text_node))
        if not text_value:
            continue
        for target in all_targets:
            if target in text_value:
                parent_length = len(_normalise_dom_text(_visible_text(parent)))
                if target not in located or parent_length <= located[target][0]:
                    consider(target, parent, parent_length)

    # If markup split a quoted phrase across inline nodes, search bounded
    # element text. Large wrappers are skipped; child elements can still match.
    unresolved = all_targets - located.keys()
    if unresolved:
        for tag in soup.find_all(True, limit=12000):
            if tag.name in {"script", "style", "noscript", "template"}:
                continue
            text_value = _normalise_dom_text(_visible_text(tag))
            if not text_value or len(text_value) > 5000:
                continue
            for target in unresolved:
                if target in text_value:
                    if target not in located or len(text_value) <= located[target][0]:
                        consider(target, tag, len(text_value))

    return [located[target][2] if target in located else None for target in targets]


# ── Definição de regras ───────────────────────────────────────
# Cada regra é uma callable: (html, text_content) -> list[ScanFinding]

RuleFn = Callable[..., list[ScanFinding]]

_RULES: list[RuleFn] = []


def _rule(fn: RuleFn) -> RuleFn:
    _RULES.append(fn)
    return fn


# ─── Regra 1: Falsa Escassez ──────────────────────────────────
# Exige quantidade ou referência explícita a estoque/oferta; chamadas vagas
# como “corra” pertencem à regra de urgência, e “acabando” sozinho é ambíguo.
_SCARCITY_RE = re.compile(
    r"""(
        (?:
          (?:s[oó](?:mente)?|apenas|somente|restam?|left|only|last)\s*
          \d+\s*(?:unidades?|itens?|pe[çc]as?|vagas?|spots?|em\s*estoque|in\s+stock)
          |
          (?:últimas?|last)\s+(?:unidades?|itens?|pe[çc]as?|vagas?|spots?)
          |
          \d+\s*(?:unidades?|itens?|pe[çc]as?|vagas?|spots?)\s+(?:restantes?|remaining|left)
        )
      |
        (?:
          (?:estoque|stock)\s+(?:limitad[oa]s?|esgotad[oa]s?|esgotand[oa])
          |
          (?:unidades?|itens?|pe[çc]as?|vagas?)\s+(?:limitad[oa]s?|esgotad[oa]s?|esgotand[oa])
          |
          (?:oferta|promo[çc][aã]o|sale)\s+(?:limitad[ao]|por\s+tempo\s+limitado)
          |
          (?:estoque|unidades?|itens?|pe[çc]as?|vagas?)\s+(?:est(?:á|ão|a|ao)\s+)?acabando
        )
    )""",
    re.IGNORECASE | re.VERBOSE,
)


@_rule
def _check_fake_scarcity(
    html: str,
    text: str,
    rendered_scarcity_candidates: list[str] | None = None,
) -> list[ScanFinding]:
    findings: list[ScanFinding] = []

    if rendered_scarcity_candidates is None:
        # Fallback for callers outside the browser-backed scan flow. The API
        # passes an explicit list, including [] when no rendered candidates exist.
        soup = _soup(html)
        candidates = [
            _visible_text(tag)
            for tag in soup.find_all(
                ["span", "p", "div", "strong", "b", "em", "small", "li", "button"],
                limit=500,
            )
        ]
    else:
        candidates = rendered_scarcity_candidates

    seen: set[str] = set()
    for t in candidates:
        t = " ".join(t.split())
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
        \b(?:hurry|corra|apresse[-\s]?se|act\s+now)\b
    )""",
    re.IGNORECASE | re.VERBOSE,
)

@_rule
def _check_fake_urgency(
    html: str,
    text: str,
    visible_countdown_evidence: list[str] | None = None,
) -> list[ScanFinding]:
    findings: list[ScanFinding] = []

    # A class name alone is not enough: the browser must confirm a visible,
    # populated countdown-like element before this higher-severity signal.
    for snippet in visible_countdown_evidence or []:
        snippet = " ".join(snippet.split())[:80]
        if not snippet:
            continue
        findings.append(ScanFinding(
            id="fake_urgency",
            type="Urgência fabricada",
            severity="high",
            evidence=f"Contador regressivo visível: \"{snippet}\"",
        ))
        break

    # Textual urgency remains medium severity; isolated words such as
    # "timer" or "countdown" are not persuasive evidence by themselves.
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


def _normalise_price(value: str) -> tuple[str, Decimal] | None:
    """Normalize a currency amount so repeated formatting is not a new price."""
    currency_match = re.match(r"(R\$|USD|\$|€|£)", value.strip(), re.IGNORECASE)
    if not currency_match:
        return None

    currency_token = currency_match.group(1).upper()
    currency = {
        "R$": "BRL",
        "USD": "USD",
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
    }[currency_token]
    amount = re.sub(r"[^\d,.]", "", value[currency_match.end():])
    if not amount or not re.search(r"\d", amount):
        return None

    if "," in amount and "." in amount:
        if amount.rfind(",") > amount.rfind("."):
            amount = amount.replace(".", "").replace(",", ".")
        else:
            amount = amount.replace(",", "")
    elif "," in amount:
        decimals = len(amount) - amount.rfind(",") - 1
        amount = amount.replace(".", "")
        if decimals in {1, 2}:
            amount = amount.replace(",", ".")
        else:
            amount = amount.replace(",", "")
    elif "." in amount:
        decimals = len(amount) - amount.rfind(".") - 1
        if decimals not in {1, 2}:
            amount = amount.replace(".", "")

    try:
        return currency, Decimal(amount)
    except InvalidOperation:
        return None


def _price_matches(text: str) -> list[tuple[str, tuple[str, Decimal]]]:
    matches: list[tuple[str, tuple[str, Decimal]]] = []
    for match in _PRICE_RE.finditer(text):
        normalized = _normalise_price(match.group(0))
        if normalized is not None:
            matches.append((match.group(0), normalized))
    return matches


@_rule
def _check_price_anchoring(html: str, text: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    soup = _soup(html)

    for sel in _PRICE_SELECTORS:
        try:
            els = soup.select(sel, limit=5)
        except Exception:
            continue
        for old_price_tag in els:
            old_prices = {
                normalized
                for _, normalized in _price_matches(_visible_text(old_price_tag))
            }
            if not old_prices:
                continue

            context: Tag | None = old_price_tag
            for _ in range(4):
                if not isinstance(context, Tag) or context.name == "[document]":
                    break

                context_text = _visible_text(context)
                if len(context_text) > 180:
                    break

                prices = _price_matches(context_text)
                has_distinct_current_price = len(old_prices) > 1 or any(
                    normalized not in old_prices for _, normalized in prices
                )
                if has_distinct_current_price:
                    findings.append(ScanFinding(
                        id="price_anchoring",
                        type="Ancoragem de preço",
                        severity="medium",
                        evidence=(
                            "Preços de referência e atual diferentes no mesmo bloco: "
                            f'"{context_text}"'
                        ),
                    ))
                    break

                parent = context.parent
                context = parent if isinstance(parent, Tag) else None

            if findings:
                break  # no máximo um finding desta regra
        if findings:
            break
    return findings[:1]  # no máximo 1 finding desta regra


# ─── Regra 5: Pré-seleção Oculta ─────────────────────────────
_OPTIN_WORDS = re.compile(
    r"(newsletter|email\s+market|promo[çc][aõ]|mailing|parceiro|oferta|publicidade)",
    re.IGNORECASE,
)


@_rule
def _check_hidden_preselection(
    html: str,
    text: str,
    visible_preselection_evidence: list[str] | None = None,
) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    seen: set[str] = set()

    for label_text in visible_preselection_evidence or []:
        label_text = " ".join(label_text.split())[:100]
        key = label_text.casefold()
        if not label_text or key in seen or not _OPTIN_WORDS.search(label_text):
            continue
        seen.add(key)
        findings.append(ScanFinding(
            id="hidden_preselection",
            type="Pré-seleção oculta",
            severity="high",
            evidence=f'Checkbox de marketing pré-selecionado: "{label_text}"',
        ))
        if len(findings) >= 2:
            break
    return findings


# ─── Regra 6: Dark Overlay / Pop-up Intrusivo ────────────────
@_rule
def _check_dark_overlay(
    html: str,
    text: str,
    visible_overlay_evidence: list[str] | None = None,
) -> list[ScanFinding]:
    """Report only browser-confirmed visible overlays with structural signals."""
    if not visible_overlay_evidence:
        return []
    snippet = " ".join(visible_overlay_evidence[0].split())[:80]
    if not snippet:
        return []
    return [ScanFinding(
        id="dark_overlay",
        type="Pop-up / overlay intrusivo",
        severity="medium",
        evidence=f'Janela sobreposta visível: "{snippet}"',
    )]


_ACCEPT_CONSENT_RE = re.compile(
    r"^(?:aceitar(?:\s+(?:todos?(?:\s+(?:os\s+)?cookies?)?|tudo|cookies?))?|"
    r"aceito(?:\s+todos?)?|accept(?:\s+(?:all|cookies?))?|"
    r"allow(?:\s+(?:all|cookies?))?|agree(?:\s+all)?|"
    r"permitir\s+todos?(?:\s+os\s+cookies?)?|concordo)$"
)
_REJECT_CONSENT_RE = re.compile(
    r"^(?:recusar(?:\s+(?:tudo|todos?(?:\s+(?:os\s+)?cookies?)?|cookies?))?|"
    r"rejeitar(?:\s+(?:tudo|todos?|todos?\s+(?:os\s+)?cookies?|cookies?))?|"
    r"reject(?:\s+(?:all|cookies?))?|decline(?:\s+all)?|refuse(?:\s+all)?|"
    r"nao\s+(?:aceitar|permitir)|apenas\s+(?:os\s+)?(?:cookies?\s+)?necessarios|"
    r"somente\s+(?:os\s+)?(?:cookies?\s+)?necessarios|only\s+(?:necessary|essential)(?:\s+cookies?)?|"
    r"necessary\s+only|continue\s+without\s+(?:accepting|cookies?)|continuar\s+sem\s+(?:aceitar|cookies?))$"
)
_MANAGE_CONSENT_RE = re.compile(
    r"(?:preferencias?|configurar|configuracoes?|personalizar|customi[sz]e|"
    r"settings?|manage|opcoes|options|gerenciar|ajustar|more\s+choices)"
)


def _normalise_consent_label(label: str) -> str:
    decomposed = unicodedata.normalize("NFKD", label.casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


@_rule
def _check_consent_asymmetry(
    html: str,
    text: str,
    consent_choice_evidence: list[dict[str, object]] | None = None,
) -> list[ScanFinding]:
    """Flag only observable imbalance between first-layer consent actions."""
    if not consent_choice_evidence:
        return []

    for panel in consent_choice_evidence:
        raw_actions = panel.get("actions")
        if not isinstance(raw_actions, list):
            continue

        actions: list[dict[str, object]] = []
        for raw_action in raw_actions:
            if not isinstance(raw_action, dict) or not isinstance(raw_action.get("label"), str):
                continue
            label = raw_action["label"].strip()
            normalized = _normalise_consent_label(label)
            if _ACCEPT_CONSENT_RE.fullmatch(normalized):
                kind = "accept"
            elif _REJECT_CONSENT_RE.fullmatch(normalized):
                kind = "reject"
            elif _MANAGE_CONSENT_RE.search(normalized):
                kind = "manage"
            else:
                continue
            try:
                prominence = float(raw_action.get("prominence", 0))
                area = max(0.0, float(raw_action.get("area", 0)))
            except (TypeError, ValueError):
                prominence, area = 0.0, 0.0
            actions.append({
                "kind": kind,
                "label": label,
                "prominence": prominence,
                "area": area,
            })

        accepts = [action for action in actions if action["kind"] == "accept"]
        rejects = [action for action in actions if action["kind"] == "reject"]
        manages = [action for action in actions if action["kind"] == "manage"]
        if not accepts:
            continue

        accept = max(accepts, key=lambda action: float(action["prominence"]))
        if not rejects:
            evidence = (
                f'Sinal heurístico: “{accept["label"]}” está visível, mas não foi '
                "identificada uma opção direta para recusar na mesma camada."
            )
            if manages:
                evidence += f' “{manages[0]["label"]}” pode abrir outras opções.'
            return [ScanFinding(
                id="consent_asymmetry",
                type="Assimetria na escolha de cookies (sinal)",
                severity="low",
                evidence=evidence,
            )]

        reject = max(rejects, key=lambda action: float(action["prominence"]))
        emphasis_gap = float(accept["prominence"]) - float(reject["prominence"])
        accept_area = float(accept["area"])
        reject_area = max(1.0, float(reject["area"]))
        much_larger = accept_area >= reject_area * 1.8
        if emphasis_gap >= 2.0 or (much_larger and emphasis_gap >= 0.5):
            return [ScanFinding(
                id="consent_asymmetry",
                type="Assimetria na escolha de cookies (sinal)",
                severity="low",
                evidence=(
                    f'Sinal heurístico: “{accept["label"]}” tem maior destaque visual '
                    f'que “{reject["label"]}” na camada de consentimento.'
                ),
            )]

    return []


# ── API pública ───────────────────────────────────────────────

def analyze(
    html: str,
    text: str,
    visible_overlay_evidence: list[str] | None = None,
    consent_choice_evidence: list[dict[str, object]] | None = None,
    visible_countdown_evidence: list[str] | None = None,
    visible_preselection_evidence: list[str] | None = None,
    rendered_scarcity_candidates: list[str] | None = None,
) -> list[ScanFinding]:
    """
    Executa todas as regras determinísticas sobre o HTML e texto da página.

    Args:
        html: HTML completo da página (document.documentElement.outerHTML).
        text: Texto visível da página (body.innerText).
        visible_overlay_evidence: textos que o Playwright confirmou como visíveis
            dentro da viewport e associados a sinais estruturais de overlay.
        consent_choice_evidence: ações visíveis de consentimento extraídas pelo
            Playwright, usadas apenas para comparar aceitar, recusar e configurar.
        visible_countdown_evidence: textos de contadores confirmados como visíveis
            pelo Playwright e com formato de tempo reconhecível.
        visible_preselection_evidence: rótulos visíveis associados a checkboxes
            marcados no estado atual e avaliados pela regra de opt-in de marketing.
        rendered_scarcity_candidates: textos curtos extraídos pelo navegador de
            elementos efetivamente renderizados, incluindo conteúdo abaixo da dobra.

    Returns:
        Lista de ScanFinding. Pode ser vazia se nenhum padrão for detectado.
    """
    all_findings: list[ScanFinding] = []
    for rule_fn in _RULES:
        try:
            if rule_fn is _check_dark_overlay:
                all_findings.extend(rule_fn(html, text, visible_overlay_evidence))
            elif rule_fn is _check_consent_asymmetry:
                all_findings.extend(rule_fn(html, text, consent_choice_evidence))
            elif rule_fn is _check_fake_urgency:
                all_findings.extend(rule_fn(html, text, visible_countdown_evidence))
            elif rule_fn is _check_hidden_preselection:
                all_findings.extend(rule_fn(html, text, visible_preselection_evidence))
            elif rule_fn is _check_fake_scarcity:
                all_findings.extend(rule_fn(html, text, rendered_scarcity_candidates))
            else:
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
